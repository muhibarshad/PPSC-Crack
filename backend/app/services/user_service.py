"""
User service — CRUD operations for users.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.exceptions import NotFound


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    """Fetch a user by primary key."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFound(f"User {user_id} not found")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[User]:
    """Return a paginated list of users."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())
