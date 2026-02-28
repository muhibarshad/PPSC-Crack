"""
PPSC Crack — Security Helpers
===============================
Supabase JWT verification, password hashing, and token cookie helpers.

Supabase issues JWTs signed with the project's JWT secret.  We verify
them server-side so that every FastAPI route can trust ``request.state.user``.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

# ═══════════════════════════════════════════════════════════
# Password Hashing (still used for local fallback / admin)
# ═══════════════════════════════════════════════════════════
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return bcrypt hash of plain-text password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Check plain-text against hashed password."""
    return pwd_context.verify(plain, hashed)


# ═══════════════════════════════════════════════════════════
# Supabase JWT Verification
# ═══════════════════════════════════════════════════════════

def verify_supabase_token(token: str) -> dict[str, Any]:
    """Decode and verify a Supabase-issued JWT.

    Returns the full payload dict on success.
    Raises ``JWTError`` on invalid / expired token.

    The token is verified against ``SUPABASE_JWT_SECRET`` using HS256.
    Supabase tokens include:
        - sub: user UUID
        - email: user email
        - role: "authenticated" | "anon"
        - aud: "authenticated"
        - exp: expiry timestamp
        - user_metadata: { name, avatar_url, ... }
        - app_metadata: { provider, providers, ... }
    """
    payload = jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=[settings.ALGORITHM],
        options={
            "verify_aud": False,  # Supabase aud varies
        },
    )
    return payload


def decode_supabase_token_unverified(token: str) -> dict[str, Any]:
    """Decode a Supabase JWT *without* signature verification.

    Useful for inspecting expired tokens during refresh flows.
    """
    return jwt.get_unverified_claims(token)


# ═══════════════════════════════════════════════════════════
# Internal Token Creation (for refresh-token rotation)
# ═══════════════════════════════════════════════════════════

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived access token (default 15 min)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a long-lived refresh token (default 7 days)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode one of *our* internally-issued tokens."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# ═══════════════════════════════════════════════════════════
# Refresh-Token Cookie Helpers
# ═══════════════════════════════════════════════════════════

REFRESH_COOKIE_NAME = "ppsc_refresh_token"
REFRESH_COOKIE_PATH = "/api/auth"  # scoped to auth routes only


def set_refresh_cookie(response, token: str) -> None:
    """Set the refresh token as an httpOnly secure cookie."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path=REFRESH_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def clear_refresh_cookie(response) -> None:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path=REFRESH_COOKIE_PATH,
    )
