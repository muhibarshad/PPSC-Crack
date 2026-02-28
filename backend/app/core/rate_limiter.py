"""
PPSC Crack — Redis-Backed Auth Rate Limiter
=============================================
Sliding-window rate limiter using Redis sorted sets.

Default: **10 auth attempts per 15 minutes per IP**.

Usage as a FastAPI dependency::

    from app.core.rate_limiter import auth_rate_limit

    @router.post("/login")
    async def login(request: Request, _=Depends(auth_rate_limit)):
        ...
"""

import time

from fastapi import Depends, HTTPException, Request, status

from app.config import settings
from app.database import get_redis

import redis.asyncio as aioredis


async def _check_rate_limit(
    redis: aioredis.Redis,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> tuple[int, int]:
    """Sliding-window counter using a Redis sorted set.

    Returns (remaining_requests, retry_after_seconds).
    Raises ``HTTPException 429`` if limit is exceeded.
    """
    now = time.time()
    window_start = now - window_seconds

    pipe = redis.pipeline()
    # Remove expired entries
    pipe.zremrangebyscore(key, 0, window_start)
    # Add current request
    pipe.zadd(key, {f"{now}": now})
    # Count entries in window
    pipe.zcard(key)
    # Set expiry on the key itself
    pipe.expire(key, window_seconds)
    results = await pipe.execute()

    request_count: int = results[2]
    remaining = max(0, max_requests - request_count)

    if request_count > max_requests:
        # Find the oldest entry to calculate retry-after
        oldest = await redis.zrange(key, 0, 0, withscores=True)
        if oldest:
            retry_after = int(window_seconds - (now - oldest[0][1])) + 1
        else:
            retry_after = window_seconds
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many auth attempts. Try again in {retry_after} seconds.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(now + retry_after)),
            },
        )

    return remaining, window_seconds


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


async def auth_rate_limit(
    request: Request,
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    """FastAPI dependency — enforce auth rate limit per IP.

    Injects ``X-RateLimit-*`` headers into the response.
    """
    client_ip = _get_client_ip(request)
    key = f"rate_limit:auth:{client_ip}"

    remaining, window = await _check_rate_limit(
        redis,
        key,
        max_requests=settings.AUTH_RATE_LIMIT_MAX,
        window_seconds=settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
    )

    # Attach rate-limit info to request state so the endpoint can
    # include it in response headers if desired
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = settings.AUTH_RATE_LIMIT_MAX
