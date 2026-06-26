"""
Rate-limit awareness and retry policy.
Separate from client.py so retry policy can change without touching HTTP logic.
"""

from __future__ import annotations

import asyncio
import time

from reviewmind.core.logging import get_logger
from reviewmind.services.github.client import GitHubClient, GitHubResponse, RateLimitError

logger = get_logger(__name__)

MAX_RETRIES = 3
BASE_BACKOFF = 2.0  # seconds; actual wait = BASE_BACKOFF ** attempt


async def get_with_retry(
    client: GitHubClient,
    path: str,
    *,
    accept: str | None = None,
    if_none_match: str | None = None,
    params: dict | None = None,
) -> GitHubResponse:
    """
    Wraps client.get() with exponential backoff on 429 / 403 rate-limit responses.
    Raises RateLimitError after MAX_RETRIES exhausted.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await client.get(
                path,
                accept=accept,
                if_none_match=if_none_match,
                params=params,
            )
        except RateLimitError as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = BASE_BACKOFF ** attempt
            logger.warning(
                "github_rate_limit_retry",
                attempt=attempt,
                wait_seconds=wait,
                status_code=exc.status_code,
            )
            await asyncio.sleep(wait)

    # unreachable but satisfies type checker
    raise RateLimitError(429, "Rate limit exceeded after retries")


def seconds_until_reset(reset_timestamp: int) -> float:
    """How many seconds until the rate-limit window resets."""
    return max(0.0, reset_timestamp - time.time())
