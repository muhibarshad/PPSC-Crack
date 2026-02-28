"""
PPSC Crack — Security Helpers
===============================
Supabase JWT verification, password hashing, and token cookie helpers.

Supabase issues JWTs signed with ES256 (ECDSA) using public JWKS.
We fetch the JWKS once at startup and verify tokens server-side so
that every FastAPI route can trust ``request.state.user``.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import logging

import bcrypt
import httpx
from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode

from app.config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# Password Hashing (still used for local fallback / admin)
# ═══════════════════════════════════════════════════════════


def hash_password(plain: str) -> str:
    """Return bcrypt hash of plain-text password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check plain-text against hashed password."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ═══════════════════════════════════════════════════════════
# Supabase JWKS Cache & JWT Verification
# ═══════════════════════════════════════════════════════════

_jwks_cache: dict[str, Any] | None = None


def _fetch_jwks() -> dict[str, Any]:
    """Fetch the JWKS from Supabase (cached after first call)."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    try:
        resp = httpx.get(jwks_url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        logger.info("Fetched Supabase JWKS (%d keys)", len(_jwks_cache.get("keys", [])))
        return _jwks_cache
    except Exception as exc:
        logger.warning("Failed to fetch JWKS from %s: %s", jwks_url, exc)
        return {"keys": []}


def _get_signing_key(token: str) -> dict[str, Any] | None:
    """Find the matching JWK for a token's kid header."""
    import json

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    alg = header.get("alg", "ES256")

    jwks = _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    # kid not found — refresh JWKS once (key rotation)
    global _jwks_cache
    _jwks_cache = None
    jwks = _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    return None


def verify_supabase_token(token: str) -> dict[str, Any]:
    """Decode and verify a Supabase-issued JWT.

    Supports both:
    - ES256 (ECDSA) tokens verified via JWKS public keys (new Supabase default)
    - HS256 (HMAC) tokens verified via SUPABASE_JWT_SECRET (legacy fallback)

    Returns the full payload dict on success.
    Raises ``JWTError`` on invalid / expired token.
    """
    # Inspect the token header to determine algorithm
    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "HS256")

    if alg in ("ES256", "ES384", "ES512", "RS256", "RS384", "RS512"):
        # Asymmetric — use JWKS public key
        signing_key = _get_signing_key(token)
        if signing_key is None:
            raise JWTError("No matching JWKS key found for token kid")

        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[alg],
            options={"verify_aud": False},
        )
        return payload
    else:
        # HS256 legacy — use JWT secret directly
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
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
