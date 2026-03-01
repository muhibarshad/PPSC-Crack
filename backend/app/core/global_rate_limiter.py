"""
PPSC Crack — Global Redis-Based Rate Limiter Middleware
========================================================
Rate limits ALL API endpoints:
  - Authenticated users: 100 requests / minute
  - Unauthenticated users: 20 requests / minute

Uses sliding-window counters via Redis sorted sets.
"""

import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.database import redis_pool

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────
RATE_LIMIT_AUTHENTICATED = int(getattr(settings, "RATE_LIMIT_AUTHENTICATED", 100))
RATE_LIMIT_UNAUTHENTICATED = int(getattr(settings, "RATE_LIMIT_UNAUTHENTICATED", 20))
RATE_LIMIT_WINDOW_SECONDS = 60  # 1 minute sliding window


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


def _is_authenticated(request: Request) -> bool:
    """Check if the request carries an Authorization header."""
    auth = request.headers.get("authorization", "")
    return auth.startswith("Bearer ") and len(auth) > 10


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter applied to every request."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for docs / health / static
        path = request.url.path
        skip_paths = ("/docs", "/redoc", "/openapi.json", "/", "/favicon.ico")
        if path in skip_paths or path.startswith("/_next"):
            return await call_next(request)

        client_ip = _get_client_ip(request)
        is_authed = _is_authenticated(request)

        max_requests = RATE_LIMIT_AUTHENTICATED if is_authed else RATE_LIMIT_UNAUTHENTICATED
        key_suffix = "auth" if is_authed else "unauth"
        key = f"rate_limit:global:{key_suffix}:{client_ip}"

        now = time.time()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS

        try:
            pipe = redis_pool.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {f"{now}": now})
            pipe.zcard(key)
            pipe.expire(key, RATE_LIMIT_WINDOW_SECONDS + 5)
            results = await pipe.execute()

            request_count: int = results[2]
            remaining = max(0, max_requests - request_count)

            if request_count > max_requests:
                oldest = await redis_pool.zrange(key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - oldest[0][1])) + 1
                else:
                    retry_after = RATE_LIMIT_WINDOW_SECONDS

                logger.warning(
                    "Rate limit exceeded: ip=%s authed=%s count=%d limit=%d",
                    client_ip, is_authed, request_count, max_requests,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Try again in {retry_after}s.",
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(now + retry_after)),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(
                int(now + RATE_LIMIT_WINDOW_SECONDS)
            )
            return response

        except Exception:
            # If Redis is down, allow the request but log the error
            logger.exception("Rate limiter Redis error — allowing request")
            return await call_next(request)
