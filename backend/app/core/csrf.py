"""
PPSC Crack — CSRF Protection Middleware
========================================
Adds CSRF token validation to all state-changing requests (POST, PUT, PATCH, DELETE).

How it works:
1. On every response, a CSRF token is set as a cookie (csrf_token).
2. State-changing requests must include the token in the X-CSRF-Token header.
3. The middleware validates the header matches the cookie.

Frontend must:
- Read the csrf_token cookie
- Include it as X-CSRF-Token header on POST/PUT/PATCH/DELETE requests
"""

import secrets
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings

logger = logging.getLogger(__name__)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
CSRF_TOKEN_LENGTH = 32

# Methods that require CSRF validation
STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths exempt from CSRF (webhooks, external callbacks, token-protected auth)
CSRF_EXEMPT_PATHS = {
    "/api/v1/payments/stripe/webhook",
    "/api/v1/payments/jazzcash/callback",
    "/api/auth/callback",
    "/api/v1/auth/callback",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/docs",
    "/redoc",
    "/openapi.json",
}


def _generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware using double-submit cookie pattern."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Skip CSRF for exempt paths
        if path in CSRF_EXEMPT_PATHS or path.startswith("/_next"):
            return await call_next(request)

        # For state-changing methods, validate CSRF token
        if request.method in STATE_CHANGING_METHODS:
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)

            if not cookie_token or not header_token:
                logger.warning(
                    "CSRF token missing: path=%s method=%s cookie=%s header=%s",
                    path, request.method, bool(cookie_token), bool(header_token),
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing. Include X-CSRF-Token header."},
                )

            if not secrets.compare_digest(cookie_token, header_token):
                logger.warning("CSRF token mismatch: path=%s method=%s", path, request.method)
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token invalid."},
                )

        # Process the request
        response = await call_next(request)

        # Set/refresh CSRF cookie on every response
        existing_token = request.cookies.get(CSRF_COOKIE_NAME)
        token = existing_token or _generate_csrf_token()

        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=token,
            httponly=False,  # JS must read this cookie
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=86400,  # 24 hours
            path="/",
        )

        return response
