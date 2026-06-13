from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from reviewmind.core.cache import redis_client
from reviewmind.db.session import get_session

router = APIRouter()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(text("SELECT 1"))
    pong = await redis_client.ping()
    return {"status": "ok", "database": "ok", "redis": "ok" if pong else "fail"}
