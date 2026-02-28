"""
Auth service — registration, login, token refresh.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import Conflict, Unauthorized


async def register_user(db: AsyncSession, email: str, password: str, full_name: str, job_type: str | None = None) -> User:
    """Create a new user after checking uniqueness."""
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise Conflict("A user with this email already exists")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        job_type=job_type,
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> dict:
    """Verify credentials and return JWT pair."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise Unauthorized("Invalid email or password")

    return {
        "access_token": create_access_token(data={"sub": str(user.id)}),
        "refresh_token": create_refresh_token(data={"sub": str(user.id)}),
        "token_type": "bearer",
    }
