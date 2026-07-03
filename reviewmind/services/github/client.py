"""
Low-level GitHub REST API client.

Knows about: HTTP, authentication, headers, ETags, pagination, error mapping.
Does NOT know about: PRs, diffs, ReviewMind business logic.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx

from reviewmind.core.config import settings
from reviewmind.core.logging import get_logger

logger = get_logger(__name__)


# ── Response wrapper ──────────────────────────────────────────────────────────

@dataclass
class RateLimit:
    limit: int = 0
    remaining: int = 5000
    reset: int = 0
    used: int = 0

    @classmethod
    def from_headers(cls, headers: httpx.Headers) -> "RateLimit":
        return cls(
            limit=int(headers.get("x-ratelimit-limit", 0)),
            remaining=int(headers.get("x-ratelimit-remaining", 5000)),
            reset=int(headers.get("x-ratelimit-reset", 0)),
            used=int(headers.get("x-ratelimit-used", 0)),
        )


@dataclass
class GitHubResponse:
    body: Any                        # parsed JSON or raw string
    status_code: int
    rate_limit: RateLimit
    etag: str | None = None

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    @property
    def not_modified(self) -> bool:
        return self.status_code == 304


# ── Exceptions ────────────────────────────────────────────────────────────────

class GitHubError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"GitHub {status_code}: {message}")


class RateLimitError(GitHubError):
    pass


class NotFoundError(GitHubError):
    pass


# ── Client ────────────────────────────────────────────────────────────────────

class GitHubClient:
    """
    Thin, disciplined wrapper around httpx.AsyncClient for the GitHub REST API.
    One instance should be shared across the application lifetime (connection pooling).
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self._token = token or settings.github_token
        self._http = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=settings.github_request_timeout,
            headers=self._default_headers(),
        )

    def _default_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": settings.github_api_version,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def close(self) -> None:
        await self._http.aclose()

    # ── Core request methods ──────────────────────────────────────────────────

    async def get(
        self,
        path: str,
        *,
        accept: str | None = None,
        if_none_match: str | None = None,
        params: dict | None = None,
    ) -> GitHubResponse:
        headers: dict[str, str] = {}
        if accept:
            headers["Accept"] = accept
        if if_none_match:
            headers["If-None-Match"] = if_none_match

        response = await self._http.get(path, headers=headers, params=params)
        rate_limit = RateLimit.from_headers(response.headers)

        self._warn_rate_limit(rate_limit)

        if response.status_code == 304:
            return GitHubResponse(body=None, status_code=304, rate_limit=rate_limit)

        if response.status_code == 404:
            raise NotFoundError(404, f"{path} not found")

        if response.status_code in (403, 429):
            raise RateLimitError(response.status_code, "Rate limit exceeded")

        if response.status_code >= 400:
            msg = response.json().get("message", response.text)
            raise GitHubError(response.status_code, msg)

        # Body: raw text for diff, JSON otherwise
        ct = response.headers.get("content-type", "")
        body = response.text if "text/" in ct or "diff" in ct else response.json()

        return GitHubResponse(
            body=body,
            status_code=response.status_code,
            rate_limit=rate_limit,
            etag=response.headers.get("etag"),
        )

    async def post(self, path: str, json: dict) -> GitHubResponse:
        response = await self._http.post(path, json=json)
        rate_limit = RateLimit.from_headers(response.headers)

        if response.status_code in (403, 429):
            raise RateLimitError(response.status_code, "Rate limit exceeded")

        if response.status_code >= 400:
            msg = response.json().get("message", response.text)
            raise GitHubError(response.status_code, msg)

        return GitHubResponse(
            body=response.json(),
            status_code=response.status_code,
            rate_limit=rate_limit,
            etag=response.headers.get("etag"),
        )

    # ── Pagination ────────────────────────────────────────────────────────────

    async def paginate(
        self, path: str, params: dict | None = None
    ) -> AsyncIterator[dict]:
        """Follow Link: rel=next until exhausted. Yields individual items."""
        url: str | None = path
        req_params = dict(params or {})
        req_params.setdefault("per_page", 100)

        while url:
            resp = await self._http.get(url, params=req_params)
            req_params = {}  # params only on first request; next URL is fully qualified

            if resp.status_code >= 400:
                raise GitHubError(resp.status_code, resp.text)

            items = resp.json()
            if isinstance(items, list):
                for item in items:
                    yield item
            else:
                yield items

            url = self._next_url(resp.headers.get("link", ""))

    @staticmethod
    def _next_url(link_header: str) -> str | None:
        for part in link_header.split(","):
            segments = part.strip().split(";")
            if len(segments) == 2 and segments[1].strip() == 'rel="next"':
                return segments[0].strip().strip("<>")
        return None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _warn_rate_limit(self, rate_limit: RateLimit) -> None:
        if 0 < rate_limit.remaining < settings.github_rate_limit_warning:
            logger.warning(
                "github_rate_limit_low",
                remaining=rate_limit.remaining,
                limit=rate_limit.limit,
            )

    # ── Context manager support ───────────────────────────────────────────────

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
