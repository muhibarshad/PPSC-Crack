"""
PPSC Crack — Shared FastAPI Dependencies
==========================================
Reusable dependency injections for routes.
"""

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, get_redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Type aliases for convenience
DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisConn = Annotated[aioredis.Redis, Depends(get_redis)]
Token = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(token: Token, db: DBSession):
    """Decode JWT and return the current user (placeholder)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # TODO: Fetch user from DB
    # user = await user_service.get_by_id(db, int(user_id))
    # if user is None:
    #     raise credentials_exception
    # return user
    return {"id": user_id}  # placeholder
