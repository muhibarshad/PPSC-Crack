"""
User model — platform users with Supabase Auth integration.

The ``supabase_uid`` column links to the Supabase Auth user record.
``password_hash`` is kept for optional local-auth fallback / admin seeding.
Roles: ``student`` (default) | ``admin`` | ``moderator``.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, JSON, Index, func, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # ── Supabase Auth link ───────────────────────────────────
    supabase_uid: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
        comment="Supabase Auth user UUID — set on first Supabase login",
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Nullable — Supabase handles auth; kept for admin seed / fallback",
    )
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    auth_provider: Mapped[str] = mapped_column(
        String(50), default="email",
        comment="email | google | magic_link",
    )

    # ── Role & access ────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        String(20), default="student", comment="student | admin | moderator"
    )
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_tier: Mapped[str] = mapped_column(
        String(20), default="free", comment="free | pro | elite"
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Stripe ───────────────────────────────────────────────
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True,
        comment="Stripe Customer ID — created on first checkout",
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True,
        comment="Active Stripe Subscription ID",
    )

    # ── Preferences ──────────────────────────────────────────
    selected_job_types: Mapped[list | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    learning_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_subscription_tier", "subscription_tier"),
        Index("ix_users_supabase_uid", "supabase_uid"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
