from __future__ import annotations

import collections
import time
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis import get_redis_client

log = structlog.get_logger(__name__)

# Fallback local in-memory sliding window cache: ip/user -> list of timestamps
_local_rate_cache: dict[str, collections.deque[float]] = collections.defaultdict(
    lambda: collections.deque(maxlen=1000)
)

ROUTE_LIMITS: dict[str, int] = {
    "/api/v1/auth/login": 10,
    "/api/v1/auth/register": 10,
    "/api/v1/coding/execute": 15,
    "/api/v1/ats/analyze": 15,
    "/api/v1/interview/session": 20,
    "/api/v1/interview/answer": 30,
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enterprise sliding-window rate limiter with Redis backend, in-memory fallback, and route-specific throttles.

    Tiered limits:
      - Default / Unauthenticated: 60 requests / minute
      - Authenticated Candidates: 120 requests / minute
      - Recruiters: 300 requests / minute
      - Admins: 600 requests / minute
      - Route-specific sensitive limits: 10 - 30 requests / minute
    """

    DEFAULT_LIMIT = 120
    WINDOW_SECONDS = 60

    # Whitelist paths from strict rate limiting (health, metrics, docs)
    EXEMPT_PATHS = {
        "/health",
        "/metrics",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/observability/health/deep",
        "/api/v1/observability/metrics/prometheus",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path in self.EXEMPT_PATHS:
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = "unlimited"
            response.headers["X-RateLimit-Remaining"] = "unlimited"
            return response

        # Extract client key: bearer token sub or IP
        auth_header = request.headers.get("Authorization")
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_key = forwarded.split(",")[0].strip()
        else:
            client_key = request.client.host if request.client else "127.0.0.1"
        limit = self.DEFAULT_LIMIT

        if auth_header and auth_header.startswith("Bearer "):
            try:
                from app.core.security import decode_access_token
                token = auth_header.split(" ", 1)[1]
                payload = decode_access_token(token)
                user_id = payload.get("sub")
                role = payload.get("role", "candidate")
                if user_id:
                    client_key = f"user:{user_id}"
                if role in ("admin", "platform_admin"):
                    limit = 600
                elif role in ("recruiter", "org_admin"):
                    limit = 300
                else:
                    limit = 120
            except Exception:
                limit = 60
        else:
            limit = 60

        # Apply route-specific throttle if matching
        for route_prefix, r_limit in ROUTE_LIMITS.items():
            if path.startswith(route_prefix):
                limit = min(limit, r_limit)
                break

        # Check rate limit using sliding window
        allowed, remaining, retry_after = await self._check_rate_limit(client_key, limit)

        if not allowed:
            log.warning("rate_limit_exceeded", client_key=client_key, path=path, limit=limit)
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit of {limit} requests per minute exceeded. Please wait.",
                    "details": {"retry_after_seconds": retry_after},
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(remaining, 0))
        response.headers["X-RateLimit-Reset"] = str(self.WINDOW_SECONDS)
        return response

    async def _check_rate_limit(self, client_key: str, limit: int) -> tuple[bool, int, int]:
        now = time.monotonic()
        window_start = now - self.WINDOW_SECONDS

        try:
            redis = get_redis_client()
            redis_key = f"ratelimit:{client_key}"
            pipe = redis.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now - self.WINDOW_SECONDS)
            pipe.zadd(redis_key, {str(now): now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, self.WINDOW_SECONDS + 5)
            results = await pipe.execute()
            count = results[2]

            remaining = limit - count
            if count > limit:
                return False, 0, self.WINDOW_SECONDS
            return True, remaining, 0
        except Exception:
            # Fallback to local sliding-window deque
            timestamps = _local_rate_cache[client_key]
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            if len(timestamps) >= limit:
                return False, 0, self.WINDOW_SECONDS

            timestamps.append(now)
            remaining = limit - len(timestamps)
            return True, remaining, 0


async def reset_rate_limit(client_key: str) -> bool:
    """Admin function to reset rate limit bucket for a client key."""
    cleared = False
    try:
        redis = get_redis_client()
        await redis.delete(f"ratelimit:{client_key}")
        cleared = True
    except Exception:
        pass

    if client_key in _local_rate_cache:
        _local_rate_cache[client_key].clear()
        cleared = True

    return cleared


async def get_client_rate_status(client_key: str, limit: int = 120) -> dict[str, Any]:
    """Retrieves current rate limit status for a client key."""
    now = time.monotonic()
    window_start = now - 60
    current_count = 0

    try:
        redis = get_redis_client()
        redis_key = f"ratelimit:{client_key}"
        await redis.zremrangebyscore(redis_key, 0, now - 60)
        current_count = await redis.zcard(redis_key)
    except Exception:
        timestamps = _local_rate_cache[client_key]
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()
        current_count = len(timestamps)

    remaining = max(0, limit - current_count)
    return {
        "client_key": client_key,
        "limit": limit,
        "remaining": remaining,
        "reset_seconds": 60,
        "is_blocked": current_count >= limit,
        "route_rules": ROUTE_LIMITS,
    }


def get_rate_limiter_overview() -> dict[str, Any]:
    """Provides high-level rate limiter operational posture."""
    return {
        "engine_status": "ONLINE",
        "algorithm": "Sliding-Window Log with Redis + In-Memory Fallback",
        "default_limit_rpm": RateLimitMiddleware.DEFAULT_LIMIT,
        "window_seconds": RateLimitMiddleware.WINDOW_SECONDS,
        "active_buckets_count": len(_local_rate_cache),
        "route_throttles": ROUTE_LIMITS,
    }
