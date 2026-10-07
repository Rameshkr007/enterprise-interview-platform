from __future__ import annotations

import structlog
from typing import AsyncGenerator
from redis.asyncio import ConnectionPool, Redis

from app.config import get_settings

log = structlog.get_logger(__name__)
settings = get_settings()

_pool: ConnectionPool | None = None


def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            str(settings.REDIS_URL),
            max_connections=50,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            health_check_interval=30,
        )
        log.info("redis_pool_initialized", url=str(settings.REDIS_URL))
    return _pool


def get_redis_client() -> Redis:
    pool = get_redis_pool()
    return Redis(connection_pool=pool)


async def check_redis_health() -> bool:
    try:
        client = get_redis_client()
        pong = await client.ping()
        return bool(pong)
    except Exception as exc:
        log.warning("redis_health_check_failed", error=str(exc))
        return False


async def close_redis_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
        log.info("redis_pool_closed")
