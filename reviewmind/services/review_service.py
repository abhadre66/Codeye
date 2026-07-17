"""
Review Service — review history, comment formatting, and guarded posting.

The post_review method requires confirmed=True to actually post to GitHub.
When confirmed=False (the default), it returns a preview so Claude can ask
the user to confirm before mutating external state.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from reviewmind.core.logging import get_logger
from reviewmind.services.github.repository import (
    GitHubRepository,
    ReviewComment,
    ReviewSummary,
)

logger = get_logger(__name__)

_SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
    "info": "⚪",
}

_VALID_EVENTS = {"APPROVE", "REQUEST_CHANGES", "COMMENT"}

_EDUCATIONAL_WHY = {
    "SEC001": "Hardcoded secrets get committed to version control and can be scraped by automated scanners. Rotate the secret immediately and move it to an environment variable.",
    "SEC002": "String interpolation in SQL queries allows attackers to alter query logic (SQL injection). Use parameterized queries or an ORM's safe query builder instead.",
    "SEC003": "This package version has a known CVE. Upgrade to a patched version to close the vulnerability.",
    "SEC004": "Passing raw user input directly to file operations or subprocess calls can lead to path traversal or command injection. Validate and sanitize before use.",
    "SEC005": "Deserializing untrusted data with pickle or unsafe yaml.load can execute arbitrary code. Use yaml.safe_load or avoid deserializing untrusted payloads.",
    "STY001": "Overly long functions are hard to test and understand. Extract logic into smaller, focused functions.",
    "STY002": "Public functions without docstrings make onboarding and maintenance harder. Add a one-line description of what the function does and its return value.",
    "STY003": "Inconsistent naming makes code harder to read. Python functions use snake_case; classes use PascalCase.",
    "STY004": "Wildcard imports pollute the namespace and make it unclear where names come from. Import explicitly.",
    "STY005": "Long lines make code harder to read in side-by-side diffs. Break the line or shorten variable names.",
    "STY006": "TODO/FIXME comments without ticket references get forgotten. Add a tracker link so the work gets scheduled.",
}


@dataclass
class ReviewHistory:
    reviews: list[ReviewSummary]
    inline_comments: list[ReviewComment]


def _split_comments(comments: list[dict] | None) -> tuple[list[dict], list[dict]]:
    """Normalize comments to GitHub's modern review-comment shape
    ({path, body, line, side}); comments without a usable path+line can't be
    anchored inline and are returned separately to be folded into the body."""
    inline: list[dict] = []
    unanchored: list[dict] = []
    for c in comments or []:
        path = c.get("path")
        body = (c.get("body") or "").strip()
        line = c.get("line")
        if not body:
            continue
        if path and line:
            inline.append({
                "path": path,
                "body": body,
                "line": int(line),
                "side": c.get("side", "RIGHT"),
            })
        else:
            unanchored.append({"path": path or "", "body": body})
    return inline, unanchored


def _fold_into_body(body: str, unanchored: list[dict]) -> str:
    if not unanchored:
        return body
    lines = [body, "", "### Other findings"]
    for c in unanchored:
        prefix = f"`{c['path']}`: " if c["path"] else ""
        lines.append(f"- {prefix}{c['body']}")
    return "\n".join(lines)


class ReviewService:

    def __init__(self, repo: GitHubRepository) -> None:
        self._repo = repo

    async def get_review_history(
        self, owner: str, repo: str, pr_number: int
    ) -> ReviewHistory:
        reviews, comments = await asyncio.gather(
            self._repo.get_pr_reviews(owner, repo, pr_number),
            self._repo.get_pr_review_comments(owner, repo, pr_number),
        )
        logger.info(
            "review_history_fetched",
            pr=pr_number,
            reviews=len(reviews),
            comments=len(comments),
        )
        return ReviewHistory(reviews=reviews, inline_comments=comments)

    def generate_review_comment(
        self,
        finding: dict,
        comment_style: str = "concise",
    ) -> str:
        rule_id = finding.get("rule_id", "")
        severity = finding.get("severity", "info")
        message = finding.get("message", "")
        snippet = finding.get("snippet", "")
        emoji = _SEVERITY_EMOJI.get(severity, "⚪")

        if comment_style == "concise":
            return f"**{rule_id}** ({severity}): {message}"

        if comment_style == "detailed":
            lines = [f"{emoji} **{rule_id}** `{severity}`", "", message]
            if snippet:
                lines += ["", "```", snippet.strip(), "```"]
            return "\n".join(lines)

        # educational
        lines = [f"{emoji} **{rule_id}** `{severity}`", "", message]
        if snippet:
            lines += ["", "```", snippet.strip(), "```"]
        why = _EDUCATIONAL_WHY.get(rule_id)
        if why:
            lines += ["", "**Why this matters:**", why]
        return "\n".join(lines)

    async def post_review(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        *,
        body: str,
        event: str,
        comments: list[dict] | None = None,
        confirmed: bool = False,
    ) -> dict:
        if event not in _VALID_EVENTS:
            raise ValueError(f"event must be one of {_VALID_EVENTS}, got {event!r}")
        if not body.strip():
            raise ValueError("body must not be empty")

        inline, unanchored = _split_comments(comments)
        full_body = _fold_into_body(body, unanchored)

        if not confirmed:
            return {
                "preview": True,
                "body": full_body,
                "event": event,
                "comments": inline,
                "warning": "Set confirmed=true to actually post this review to GitHub.",
            }

        result = await self._repo.post_review(
            owner, repo, pr_number,
            body=full_body,
            event=event,
            comments=inline,
        )
        logger.info("review_posted", pr=pr_number, review_event=event, id=result.get("id"))
        return result
