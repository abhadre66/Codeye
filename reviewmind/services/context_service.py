"""
Context Service — enriches a PR with who touched the code and what's related.

Provides:
  - get_pr_context: recent committers, related PRs, linked issues
  - suggest_reviewers: ranked by commit frequency + CODEOWNERS match
"""

from __future__ import annotations

import asyncio
import fnmatch
import re
from dataclasses import dataclass, field

from reviewmind.core.logging import get_logger
from reviewmind.services.github.repository import (
    CommitSummary,
    GitHubRepository,
    IssueSummary,
    PRSummary,
)

logger = get_logger(__name__)

_ISSUE_REF_RE = re.compile(
    r"(?:closes?|fixes?|resolves?)\s+#(\d+)|(?<!\w)#(\d+)",
    re.IGNORECASE,
)


@dataclass
class FileContributor:
    username: str
    commit_count: int
    last_commit_message: str


@dataclass
class PRContext:
    pr: PRSummary
    file_contributors: dict[str, list[FileContributor]]
    related_prs: list[PRSummary]
    linked_issues: list[IssueSummary]


@dataclass
class ReviewerSuggestion:
    username: str
    score: int
    reasons: list[str] = field(default_factory=list)


class ContextService:

    def __init__(self, repo: GitHubRepository) -> None:
        self._repo = repo

    async def get_pr_context(
        self, owner: str, repo: str, pr_number: int
    ) -> PRContext:
        pr = await self._repo.get_pr(owner, repo, pr_number)
        files = await self._repo.get_pr_files(owner, repo, pr_number)
        file_paths = [f.filename for f in files]

        issue_numbers = self._parse_issue_numbers(pr.body)
        commits_by_file, related_prs, linked_issues = await asyncio.gather(
            self._repo.get_commits_for_files(owner, repo, file_paths),
            self._repo.get_related_prs(owner, repo, file_paths),
            self._repo.get_linked_issues(owner, repo, issue_numbers),
        )

        logger.info(
            "pr_context_fetched",
            pr=pr_number,
            files=len(file_paths),
            related_prs=len(related_prs),
            linked_issues=len(linked_issues),
        )
        return PRContext(
            pr=pr,
            file_contributors=self._build_contributors(commits_by_file),
            related_prs=related_prs,
            linked_issues=linked_issues,
        )

    async def suggest_reviewers(
        self, owner: str, repo: str, pr_number: int
    ) -> list[ReviewerSuggestion]:
        pr = await self._repo.get_pr(owner, repo, pr_number)
        files = await self._repo.get_pr_files(owner, repo, pr_number)
        file_paths = [f.filename for f in files]

        commits_by_file, codeowners_raw = await asyncio.gather(
            self._repo.get_commits_for_files(owner, repo, file_paths),
            self._repo.get_codeowners(owner, repo),
        )

        suggestions = self._rank_reviewers(
            pr.author, commits_by_file, codeowners_raw, file_paths
        )
        logger.info("pr_reviewer_suggestions", pr=pr_number, count=len(suggestions))
        return suggestions

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse_issue_numbers(self, pr_body: str) -> list[int]:
        numbers: list[int] = []
        for m in _ISSUE_REF_RE.finditer(pr_body):
            n = m.group(1) or m.group(2)
            if n:
                numbers.append(int(n))
        return list(dict.fromkeys(numbers))  # deduplicate, preserve order

    def _build_contributors(
        self, commits_by_file: dict[str, list[CommitSummary]]
    ) -> dict[str, list[FileContributor]]:
        result: dict[str, list[FileContributor]] = {}
        for filename, commits in commits_by_file.items():
            counts: dict[str, int] = {}
            last_msg: dict[str, str] = {}
            for commit in commits:
                author = commit.author
                counts[author] = counts.get(author, 0) + 1
                if author not in last_msg:
                    last_msg[author] = commit.message
            result[filename] = [
                FileContributor(
                    username=author,
                    commit_count=count,
                    last_commit_message=last_msg[author],
                )
                for author, count in sorted(counts.items(), key=lambda kv: -kv[1])
            ]
        return result

    def _rank_reviewers(
        self,
        pr_author: str,
        commits_by_file: dict[str, list[CommitSummary]],
        codeowners_raw: str,
        file_paths: list[str],
    ) -> list[ReviewerSuggestion]:
        scores: dict[str, int] = {}
        reasons: dict[str, list[str]] = {}

        # +1 per commit to a touched file
        for filename, commits in commits_by_file.items():
            for commit in commits:
                user = commit.author
                if user == pr_author:
                    continue
                scores[user] = scores.get(user, 0) + 1
                reasons.setdefault(user, [])
                label = f"recent commit to `{filename}`"
                if label not in reasons[user]:
                    reasons[user].append(label)

        # +3 per CODEOWNERS match
        for line in codeowners_raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            pattern = parts[0].lstrip("/")
            owners = [p.lstrip("@").split("/")[-1] for p in parts[1:]]
            for file_path in file_paths:
                if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(
                    file_path, f"**/{pattern}"
                ):
                    for owner in owners:
                        if owner == pr_author:
                            continue
                        scores[owner] = scores.get(owner, 0) + 3
                        reasons.setdefault(owner, [])
                        label = f"CODEOWNER of `{pattern}`"
                        if label not in reasons[owner]:
                            reasons[owner].append(label)

        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        return [
            ReviewerSuggestion(
                username=user,
                score=score,
                reasons=reasons.get(user, [])[:3],
            )
            for user, score in ranked[:5]
        ]
