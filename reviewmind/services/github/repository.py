"""
High-level GitHub service — ReviewMind's view of what it needs from GitHub.

Knows about: PRs, diffs, files, reviews.
Does NOT know about: HTTP details (that's client.py), caching TTLs (that's cache.py).
"""

from __future__ import annotations

from dataclasses import dataclass

from reviewmind.core.cache import (
    cache_aside,
    delete,
    etag_key,
    get_json,
    pr_key,
    set_json,
)
from reviewmind.core.logging import get_logger
from reviewmind.services.github.client import GitHubClient
from reviewmind.services.github.rate_limiter import get_with_retry

logger = get_logger(__name__)

# TTLs (seconds)
TTL_PR_OPEN   = 5 * 60       # 5 min  — open PRs change often
TTL_PR_CLOSED = 24 * 60 * 60 # 24 h   — closed/merged are immutable
TTL_DIFF_OPEN = 60 * 60      # 1 h
TTL_DIFF_CLOSED = 7 * 24 * 60 * 60  # 7 days


# ── Pydantic-free data models (plain dataclasses for speed) ──────────────────

@dataclass
class PRSummary:
    number: int
    title: str
    author: str
    state: str          # open | closed | merged
    base_branch: str
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

    # ── Cache invalidation ────────────────────────────────────────────────────

    async def invalidate_pr(self, owner: str, repo: str, number: int) -> None:
        """Call this on webhook pull_request.synchronize events."""
        for suffix in ("summary", "diff", "files", "analysis"):
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
        head_sha=data["head"]["sha"],
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        changed_files=data.get("changed_files", 0),
        body=data.get("body") or "",
        url=data["html_url"],
        owner=owner,
        repo=repo,
    )


def _dict_to_pr_file(data: dict) -> PRFile:
    return PRFile(
        filename=data["filename"],
        status=data["status"],
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        patch=data.get("patch", ""),
    )
