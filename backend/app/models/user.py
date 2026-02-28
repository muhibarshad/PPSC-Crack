"""
User model — platform users with subscription & learning progress.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, JSON, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Role & access ────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        String(20), default="user", comment="user | admin | moderator"
    )
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    subscription_tier: Mapped[str] = mapped_column(
        String(20), default="free", comment="free | pro | elite"
    )
    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Preferences ──────────────────────────────────────────
    selected_job_types: Mapped[list | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=True
    )
    learning_progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── Indexes ──────────────────────────────────────────────
    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_subscription_tier", "subscription_tier"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
