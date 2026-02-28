"""CRUD helpers for **User** model — Supabase Auth integrated."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """Extended CRUD for users table with Supabase-aware auth helpers."""

    # ── Override create — password is optional for Supabase users ──

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """Create a user.  Password is hashed only when provided."""
        data = obj_in.model_dump(exclude={"password"})
        if obj_in.password:
            data["password_hash"] = hash_password(obj_in.password)
        else:
            data["password_hash"] = None
        db_obj = self.model(**data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    # ── Supabase-specific lookups ────────────────────────────

    async def get_by_supabase_uid(
        self, db: AsyncSession, *, uid: str
    ) -> User | None:
        """Find a user by their Supabase Auth UUID."""
        result = await db.execute(
            select(self.model).where(self.model.supabase_uid == uid)
        )
        return result.scalar_one_or_none()

    async def get_or_create_from_supabase(
        self,
        db: AsyncSession,
        *,
        supabase_uid: str,
        email: str,
        name: str,
        avatar_url: str | None = None,
        auth_provider: str = "email",
    ) -> tuple[User, bool]:
        """Find user by supabase_uid, or create one.  Returns (user, created)."""
        user = await self.get_by_supabase_uid(db, uid=supabase_uid)
        if user:
            return user, False

        # Also check by email (existing account from before Supabase)
        user = await self.get_by_email(db, email=email)
        if user:
            # Link existing account to Supabase
            user.supabase_uid = supabase_uid
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            if auth_provider != "email":
                user.auth_provider = auth_provider
            db.add(user)
            await db.flush()
            await db.refresh(user)
            return user, False

        # Brand-new user
        new_user = self.model(
            supabase_uid=supabase_uid,
            email=email,
            name=name,
            avatar_url=avatar_url,
            auth_provider=auth_provider,
            role="student",
        )
        db.add(new_user)
        await db.flush()
        await db.refresh(new_user)
        return new_user, True

    # ── Standard lookups ─────────────────────────────────────

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """Find a user by email address."""
        result = await db.execute(select(self.model).where(self.model.email == email))
        return result.scalar_one_or_none()

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> User | None:
        """Verify email + password (local fallback), return User or None."""
        user = await self.get_by_email(db, email=email)
        if user is None:
            return None
        if not user.password_hash:
            return None  # Supabase-only user has no local password
        if not verify_password(password, user.password_hash):
            return None
        return user

    # ── Role / subscription ──────────────────────────────────

    async def get_admins(self, db: AsyncSession) -> list[User]:
        """Return all admin users."""
        result = await db.execute(
            select(self.model).where(self.model.role == "admin")
        )
        return list(result.scalars().all())

    async def get_premium_users(self, db: AsyncSession) -> list[User]:
        """Return all premium subscribers."""
        result = await db.execute(
            select(self.model).where(self.model.is_premium.is_(True))
        )
        return list(result.scalars().all())

    async def set_role(
        self, db: AsyncSession, *, id: UUID, role: str
    ) -> User:
        """Change a user's role (user / admin / moderator)."""
        return await self.update(db, id=id, obj_in={"role": role})

    async def set_subscription(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        tier: str,
        expires_at=None,
    ) -> User:
        """Update subscription tier and expiry."""
        update_data: dict = {
            "subscription_tier": tier,
            "is_premium": tier != "free",
        }
        if expires_at is not None:
            update_data["subscription_expires_at"] = expires_at
        return await self.update(db, id=id, obj_in=update_data)

    async def update_learning_progress(
        self, db: AsyncSession, *, id: UUID, progress: dict
    ) -> User:
        """Replace the learning_progress JSON blob."""
        return await self.update(db, id=id, obj_in={"learning_progress": progress})

    async def set_selected_job_types(
        self, db: AsyncSession, *, id: UUID, job_type_ids: list[UUID]
    ) -> User:
        """Set the user's selected job types for personalized study."""
        return await self.update(db, id=id, obj_in={"selected_job_types": job_type_ids})


crud_user = CRUDUser(User)
