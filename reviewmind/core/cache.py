import json
from typing import Any, Callable, Awaitable

import redis.asyncio as redis

from reviewmind.core.config import settings

redis_client: redis.Redis = redis.from_url(settings.redis_url, decode_responses=True)


async def get_json(key: str) -> Any | None:
    raw = await redis_client.get(key)
    return json.loads(raw) if raw is not None else None


async def set_json(key: str, value: Any, ttl_seconds: int) -> None:
    await redis_client.set(key, json.dumps(value), ex=ttl_seconds)


async def delete(key: str) -> None:
    await redis_client.delete(key)


# ── Cache key builders ────────────────────────────────────────────────────────

def pr_key(owner: str, repo: str, number: int, suffix: str) -> str:
    """e.g. pr:acme:widgets:42:summary"""
    return f"pr:{owner}:{repo}:{number}:{suffix}"


def repo_key(owner: str, repo: str, suffix: str) -> str:
    """e.g. repo:acme:widgets:config"""
    return f"repo:{owner}:{repo}:{suffix}"


def etag_key(owner: str, repo: str, number: int, suffix: str) -> str:
    return f"etag:{owner}:{repo}:{number}:{suffix}"


# ── Cache-aside helper ────────────────────────────────────────────────────────

async def cache_aside(
    key: str,
    fetch_fn: Callable[[], Awaitable[Any]],
    ttl_seconds: int,
) -> tuple[Any, bool]:
    """
    Check Redis first. On miss, call fetch_fn(), store result, return it.
    Returns (value, cache_hit: bool).
    """
    cached = await get_json(key)
    if cached is not None:
        return cached, True
    value = await fetch_fn()
    if value is not None:
        await set_json(key, value, ttl_seconds)
    return value, False
