import json
from typing import Any

import redis.asyncio as redis

from reviewmind.core.config import settings

redis_client: redis.Redis = redis.from_url(settings.redis_url, decode_responses=True)


async def get_json(key: str) -> Any | None:
    raw = await redis_client.get(key)
    return json.loads(raw) if raw is not None else None


async def set_json(key: str, value: Any, ttl_seconds: int) -> None:
    await redis_client.set(key, json.dumps(value), ex=ttl_seconds)
