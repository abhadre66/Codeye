"""
High-level GitHub service — ReviewMind's view of what it needs from GitHub.

Knows about: PRs, diffs, files, reviews.
Does NOT know about: HTTP details (that's client.py), caching TTLs (that's cache.py).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from reviewmind.core.cache import (
    cache_aside,
    delete,
    etag_key,
    get_json,
    pr_key,
    repo_key,
    set_json,
)
from reviewmind.core.logging import get_logger
from reviewmind.services.github.client import GitHubClient, NotFoundError
from reviewmind.services.github.rate_limiter import get_with_retry

logger = get_logger(__name__)

# TTLs (seconds)
TTL_PR_OPEN    = 5 * 60              # 5 min  — open PRs change often
TTL_PR_CLOSED  = 24 * 60 * 60       # 24 h   — closed/merged are immutable
TTL_DIFF_OPEN  = 60 * 60            # 1 h
TTL_DIFF_CLOSED = 7 * 24 * 60 * 60  # 7 days
TTL_COMMITS    = 30 * 60            # 30 min
TTL_CODEOWNERS = 60 * 60            # 1 h
TTL_CHECKS     = 2 * 60             # 2 min  — CI status is volatile
TTL_REVIEWS    = 5 * 60             # 5 min
TTL_REPO_PRS   = 10 * 60            # 10 min


# ── Pydantic-free data models (plain dataclasses for speed) ──────────────────

@dataclass
class PRSummary:
    number: int
    title: str
    author: str
    state: str          # open | closed | merged
    base_branch: str
    base_sha: str
    head_sha: str
    additions: int
    deletions: int
    changed_files: int
    body: str
    url: str
    owner: str
    repo: str


@dataclass
class PRFile:
    filename: str
    status: str         # added | modified | removed | renamed
    additions: int
    deletions: int
    patch: str          # unified diff for this file (may be empty for binary)


@dataclass
class CommitSummary:
    sha: str
    message: str        # first line only
    author: str
    authored_at: str    # ISO timestamp


@dataclass
class IssueSummary:
    number: int
    title: str
    state: str          # open | closed
    body: str
    url: str


@dataclass
class CheckRun:
    name: str
    status: str                  # queued | in_progress | completed
    conclusion: str | None       # success | failure | neutral | cancelled | skipped | timed_out
    url: str


@dataclass
class ReviewSummary:
    id: int
    author: str
    state: str          # APPROVED | CHANGES_REQUESTED | COMMENTED | PENDING | DISMISSED
    body: str
    submitted_at: str


@dataclass
class ReviewComment:
    id: int
    path: str
    line: int | None
    body: str
    author: str
    created_at: str


@dataclass
class RepoSummary:
    owner: str
    name: str
    full_name: str
    private: bool
    description: str
    default_branch: str
    pushed_at: str
    open_issues: int


@dataclass
class PRListItem:
    number: int
    title: str
    author: str
    head_branch: str
    base_branch: str
    updated_at: str
    draft: bool
    url: str


# ── Repository service ────────────────────────────────────────────────────────

class GitHubRepository:

    def __init__(self, client: GitHubClient) -> None:
        self._client = client

    # ── PR Summary ────────────────────────────────────────────────────────────

    async def get_pr(self, owner: str, repo: str, number: int) -> PRSummary:
        cache_key = pr_key(owner, repo, number, "summary")
        e_key = etag_key(owner, repo, number, "summary")
        path = f"/repos/{owner}/{repo}/pulls/{number}"

        # Check ETag — 304 means nothing changed, serve cache
        stored_etag = await get_json(e_key)
        resp = await get_with_retry(
            self._client,
            path,
            if_none_match=stored_etag,
        )

        if resp.not_modified:
            cached = await get_json(cache_key)
            logger.info("github_cache_hit", key=cache_key, source="etag")
            return _dict_to_pr_summary(cached, owner, repo)

        summary = _dict_to_pr_summary(resp.body, owner, repo)
        ttl = TTL_PR_OPEN if summary.state == "open" else TTL_PR_CLOSED

        await set_json(cache_key, resp.body, ttl)
        if resp.etag:
            await set_json(e_key, resp.etag, ttl)

        logger.info("github_cache_miss", key=cache_key, state=summary.state)
        return summary

    # ── Raw diff ─────────────────────────────────────────────────────────────

    async def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        cache_key = pr_key(owner, repo, number, "diff")

        async def fetch() -> str:
            resp = await get_with_retry(
                self._client,
                f"/repos/{owner}/{repo}/pulls/{number}",
                accept="application/vnd.github.v3.diff",
            )
            return resp.body  # raw diff string

        diff, hit = await cache_aside(cache_key, fetch, TTL_DIFF_OPEN)
        logger.info("github_diff", key=cache_key, cache_hit=hit)
        return diff

    # ── Changed files ─────────────────────────────────────────────────────────

    async def get_pr_files(
        self, owner: str, repo: str, number: int
    ) -> list[PRFile]:
        cache_key = pr_key(owner, repo, number, "files")

        async def fetch() -> list[dict]:
            items = []
            async for item in self._client.paginate(
                f"/repos/{owner}/{repo}/pulls/{number}/files"
            ):
                items.append(item)
            return items

        raw_files, hit = await cache_aside(cache_key, fetch, TTL_DIFF_OPEN)
        logger.info("github_files", key=cache_key, cache_hit=hit)
        return [_dict_to_pr_file(f) for f in raw_files]

    # ── File content ──────────────────────────────────────────────────────────

    async def get_file_content(
        self, owner: str, repo: str, path: str, ref: str
    ) -> str:
        """Fetch the full content of a file at a specific commit SHA."""
        import base64

        resp = await get_with_retry(
            self._client,
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": ref},
        )
        # GitHub returns base64-encoded content
        return base64.b64decode(resp.body["content"]).decode("utf-8")

    # ── Post review ───────────────────────────────────────────────────────────

    async def post_review(
        self,
        owner: str,
        repo: str,
        number: int,
        *,
        body: str,
        event: str,
        comments: list[dict] | None = None,
    ) -> dict:
        """
        event: APPROVE | REQUEST_CHANGES | COMMENT
        comments: [{"path": str, "line": int, "body": str}]
        """
        payload: dict = {"body": body, "event": event}
        if comments:
            payload["comments"] = comments

        resp = await self._client.post(
            f"/repos/{owner}/{repo}/pulls/{number}/reviews",
            json=payload,
        )
        logger.info(
            "github_review_posted",
            owner=owner,
            repo=repo,
            pr=number,
            event=event,
            review_id=resp.body.get("id"),
        )
        return resp.body

    # ── Commits per file ─────────────────────────────────────────────────────────

    async def get_commits_for_files(
        self, owner: str, repo: str, files: list[str]
    ) -> dict[str, list[CommitSummary]]:
        """Return up to 10 recent commits per file. Caps at 20 files to stay within rate limits."""
        capped = files[:20]

        async def _fetch_one(filename: str) -> tuple[str, list[CommitSummary]]:
            key = repo_key(owner, repo, f"commits:{filename}")

            async def fetch() -> list[dict]:
                resp = await get_with_retry(
                    self._client,
                    f"/repos/{owner}/{repo}/commits",
                    params={"path": filename, "per_page": 10},
                )
                return resp.body if isinstance(resp.body, list) else []

            raw, hit = await cache_aside(key, fetch, TTL_COMMITS)
            logger.info("github_commits_for_file", file=filename, cache_hit=hit)
            return filename, [_dict_to_commit_summary(c) for c in (raw or [])]

        results = await asyncio.gather(*[_fetch_one(f) for f in capped])
        return dict(results)

    # ── Related PRs ───────────────────────────────────────────────────────────

    async def get_related_prs(
        self, owner: str, repo: str, file_paths: list[str], state: str = "all"
    ) -> list[PRSummary]:
        """Return up to 20 recent PRs for the repo."""
        key = repo_key(owner, repo, f"recent_prs:{state}")

        async def fetch() -> list[dict]:
            items: list[dict] = []
            async for item in self._client.paginate(
                f"/repos/{owner}/{repo}/pulls",
                params={"state": state, "per_page": 20},
            ):
                items.append(item)
                if len(items) >= 20:
                    break
            return items

        raw, hit = await cache_aside(key, fetch, TTL_REPO_PRS)
        logger.info("github_related_prs", owner=owner, repo=repo, cache_hit=hit)
        return [_dict_to_pr_summary(d, owner, repo) for d in (raw or [])]

    # ── Browse: user repos & open PRs ─────────────────────────────────────────

    async def list_user_repos(
        self, *, per_page: int = 100, page: int = 1
    ) -> list[RepoSummary]:
        """Repos the token's user owns, collaborates on, or gets via an org.

        Deliberately uncached: results are token-scoped, and the shared
        repo_key-style cache keys would leak one user's private repo list
        to another.
        """
        resp = await get_with_retry(
            self._client,
            "/user/repos",
            params={
                "sort": "pushed",
                "per_page": per_page,
                "page": page,
                "affiliation": "owner,collaborator,organization_member",
            },
        )
        raw = resp.body if isinstance(resp.body, list) else []
        return [_dict_to_repo_summary(d) for d in raw]

    async def list_open_prs(
        self, owner: str, repo: str, *, per_page: int = 50
    ) -> list[PRListItem]:
        """Open PRs for a repo, most recently updated first. Uncached: may be
        private data, and users expect a fresh list when picking a PR."""
        resp = await get_with_retry(
            self._client,
            f"/repos/{owner}/{repo}/pulls",
            params={
                "state": "open",
                "sort": "updated",
                "direction": "desc",
                "per_page": per_page,
            },
        )
        raw = resp.body if isinstance(resp.body, list) else []
        return [_dict_to_pr_list_item(d) for d in raw]

    # ── Linked issues ─────────────────────────────────────────────────────────

    async def get_linked_issues(
        self, owner: str, repo: str, issue_numbers: list[int]
    ) -> list[IssueSummary]:
        """Fetch issue details for a list of issue numbers (concurrently)."""
        if not issue_numbers:
            return []

        async def _fetch_one(number: int) -> IssueSummary | None:
            key = repo_key(owner, repo, f"issue:{number}")

            async def fetch() -> dict:
                resp = await get_with_retry(
                    self._client,
                    f"/repos/{owner}/{repo}/issues/{number}",
                )
                return resp.body

            try:
                raw, hit = await cache_aside(key, fetch, 30 * 60)
                logger.info("github_issue", number=number, cache_hit=hit)
                return _dict_to_issue_summary(raw)
            except NotFoundError:
                return None

        results = await asyncio.gather(*[_fetch_one(n) for n in issue_numbers])
        return [r for r in results if r is not None]

    # ── CODEOWNERS ───────────────────────────────────────────────────────────

    async def get_codeowners(self, owner: str, repo: str) -> str:
        """Return raw CODEOWNERS content, or '' if no file exists."""
        key = repo_key(owner, repo, "codeowners")
        cached = await get_json(key)
        if cached is not None:
            return cached

        for path in (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS"):
            try:
                content = await self.get_file_content(owner, repo, path, "HEAD")
                await set_json(key, content, TTL_CODEOWNERS)
                logger.info("github_codeowners", path=path)
                return content
            except NotFoundError:
                continue

        await set_json(key, "", TTL_CODEOWNERS)
        return ""

    # ── CI check runs ────────────────────────────────────────────────────────

    async def get_check_runs(self, owner: str, repo: str, ref: str) -> list[CheckRun]:
        """Return CI check runs for a commit ref."""
        key = repo_key(owner, repo, f"checks:{ref}")

        async def fetch() -> list[dict]:
            resp = await get_with_retry(
                self._client,
                f"/repos/{owner}/{repo}/commits/{ref}/check-runs",
            )
            return resp.body.get("check_runs", []) if isinstance(resp.body, dict) else []

        raw, hit = await cache_aside(key, fetch, TTL_CHECKS)
        logger.info("github_check_runs", ref=ref, cache_hit=hit)
        return [_dict_to_check_run(c) for c in (raw or [])]

    # ── PR reviews ───────────────────────────────────────────────────────────

    async def get_pr_reviews(
        self, owner: str, repo: str, number: int
    ) -> list[ReviewSummary]:
        """Return all submitted reviews on a PR."""
        key = pr_key(owner, repo, number, "reviews")

        async def fetch() -> list[dict]:
            items: list[dict] = []
            async for item in self._client.paginate(
                f"/repos/{owner}/{repo}/pulls/{number}/reviews"
            ):
                items.append(item)
            return items

        raw, hit = await cache_aside(key, fetch, TTL_REVIEWS)
        logger.info("github_pr_reviews", pr=number, cache_hit=hit)
        return [_dict_to_review_summary(r) for r in (raw or [])]

    # ── PR review comments ────────────────────────────────────────────────────

    async def get_pr_review_comments(
        self, owner: str, repo: str, number: int
    ) -> list[ReviewComment]:
        """Return all inline review comments on a PR."""
        key = pr_key(owner, repo, number, "review_comments")

        async def fetch() -> list[dict]:
            items: list[dict] = []
            async for item in self._client.paginate(
                f"/repos/{owner}/{repo}/pulls/{number}/comments"
            ):
                items.append(item)
            return items

        raw, hit = await cache_aside(key, fetch, TTL_REVIEWS)
        logger.info("github_pr_review_comments", pr=number, cache_hit=hit)
        return [_dict_to_review_comment(c) for c in (raw or [])]

    # ── Cache invalidation ────────────────────────────────────────────────────

    async def invalidate_pr(self, owner: str, repo: str, number: int) -> None:
        """Call this on webhook pull_request.synchronize events."""
        for suffix in ("summary", "diff", "files", "analysis", "reviews", "review_comments"):
            await delete(pr_key(owner, repo, number, suffix))
        logger.info("github_cache_invalidated", owner=owner, repo=repo, pr=number)


# ── Mapping helpers ───────────────────────────────────────────────────────────

def _dict_to_pr_summary(data: dict, owner: str, repo: str) -> PRSummary:
    return PRSummary(
        number=data["number"],
        title=data["title"],
        author=data["user"]["login"],
        state=data["state"],
        base_branch=data["base"]["ref"],
        base_sha=data["base"]["sha"],
        head_sha=data["head"]["sha"],
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        changed_files=data.get("changed_files", 0),
        body=data.get("body") or "",
        url=data["html_url"],
        owner=owner,
        repo=repo,
    )


def _dict_to_repo_summary(data: dict) -> RepoSummary:
    return RepoSummary(
        owner=data["owner"]["login"],
        name=data["name"],
        full_name=data["full_name"],
        private=data.get("private", False),
        description=data.get("description") or "",
        default_branch=data.get("default_branch", "main"),
        pushed_at=data.get("pushed_at") or "",
        open_issues=data.get("open_issues_count", 0),
    )


def _dict_to_pr_list_item(data: dict) -> PRListItem:
    return PRListItem(
        number=data["number"],
        title=data["title"],
        author=data["user"]["login"],
        head_branch=data["head"]["ref"],
        base_branch=data["base"]["ref"],
        updated_at=data.get("updated_at") or "",
        draft=data.get("draft", False),
        url=data["html_url"],
    )


def _dict_to_pr_file(data: dict) -> PRFile:
    return PRFile(
        filename=data["filename"],
        status=data["status"],
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        patch=data.get("patch", ""),
    )


def _dict_to_commit_summary(data: dict) -> CommitSummary:
    commit = data.get("commit", {})
    author = commit.get("author") or {}
    return CommitSummary(
        sha=data.get("sha", ""),
        message=(commit.get("message") or "").split("\n")[0],
        author=data.get("author", {}).get("login") or author.get("name", "unknown"),
        authored_at=author.get("date", ""),
    )


def _dict_to_issue_summary(data: dict) -> IssueSummary:
    return IssueSummary(
        number=data["number"],
        title=data.get("title", ""),
        state=data.get("state", ""),
        body=data.get("body") or "",
        url=data.get("html_url", ""),
    )


def _dict_to_check_run(data: dict) -> CheckRun:
    return CheckRun(
        name=data.get("name", ""),
        status=data.get("status", ""),
        conclusion=data.get("conclusion"),
        url=data.get("html_url", ""),
    )


def _dict_to_review_summary(data: dict) -> ReviewSummary:
    return ReviewSummary(
        id=data.get("id", 0),
        author=data.get("user", {}).get("login", "unknown"),
        state=data.get("state", ""),
        body=data.get("body") or "",
        submitted_at=data.get("submitted_at", ""),
    )


def _dict_to_review_comment(data: dict) -> ReviewComment:
    return ReviewComment(
        id=data.get("id", 0),
        path=data.get("path", ""),
        line=data.get("line"),
        body=data.get("body") or "",
        author=data.get("user", {}).get("login", "unknown"),
        created_at=data.get("created_at", ""),
    )
