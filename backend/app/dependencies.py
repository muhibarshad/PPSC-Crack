"""
PPSC Crack — Shared FastAPI Dependencies
==========================================
Supabase JWT verification  →  local User resolution  →  role gates.
"""

from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import verify_supabase_token, decode_token
from app.database import get_db, get_redis
from app.models.user import User

# ── Bearer token extractor (works with Supabase JWTs) ──────
bearer_scheme = HTTPBearer(auto_error=False)

# Type aliases for convenience
DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisConn = Annotated[aioredis.Redis, Depends(get_redis)]


async def _extract_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Pull the raw JWT string from the Authorization header."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


Token = Annotated[str, Depends(_extract_token)]


async def get_current_user(token: Token, db: DBSession) -> User:
    """Verify the JWT and return the local User ORM object.

    Flow:
    1. Try decoding as a Supabase-issued JWT (``SUPABASE_JWT_SECRET``).
    2. If that fails, fall back to our own internal JWT (``SECRET_KEY``).
    3. Resolve the ``sub`` claim to a local User row.
    """
    from app.crud import crud_user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload: dict | None = None
    user_id: str | None = None

    # ── Attempt 1: Supabase JWT ──────────────────────────────
    try:
        payload = verify_supabase_token(token)
        supabase_uid: str | None = payload.get("sub")
        if supabase_uid:
            # Resolve by supabase_uid first
            user = await crud_user.get_by_supabase_uid(db, uid=supabase_uid)
            if user:
                return user
            # Auto-provision from Supabase token metadata
            email = payload.get("email", "")
            meta = payload.get("user_metadata", {})
            name = meta.get("full_name") or meta.get("name") or email.split("@")[0]
            avatar = meta.get("avatar_url")
            provider = (payload.get("app_metadata", {}).get("provider", "email"))
            user, _ = await crud_user.get_or_create_from_supabase(
                db,
                supabase_uid=supabase_uid,
                email=email,
                name=name,
                avatar_url=avatar,
                auth_provider=provider,
            )
            await db.commit()
            return user
    except JWTError:
        pass  # Not a Supabase token — try internal

    # ── Attempt 2: Internal JWT (our own refresh-rotated tokens) ─
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except JWTError:
        raise credentials_exception

    if not user_id:
        raise credentials_exception

    user = await crud_user.get(db, id=UUID(user_id))
    if user is None:
        raise credentials_exception
    return user


# ── Role gates ──────────────────────────────────────────────

async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require JWT + role='admin'."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_student(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require JWT + role='student' (or admin, who can do everything)."""
    if current_user.role not in ("student", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student or admin role required",
        )
    return current_user


async def require_premium(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the user to have an active premium subscription."""
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return current_user
