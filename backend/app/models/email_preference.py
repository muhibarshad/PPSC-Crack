"""
Email Preference model — per-user opt-in/out for each transactional email type.

Stored separately from User for clean separation of concerns.
Defaults are all ``True`` — users opt OUT of emails they don't want.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EmailPreference(Base):
    __tablename__ = "email_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Email Categories ──────────────────────────────────────
    welcome: Mapped[bool] = mapped_column(Boolean, default=True, comment="Welcome email on registration")
    subscription_confirmation: Mapped[bool] = mapped_column(Boolean, default=True, comment="Payment / subscription confirmation")
    subscription_expiry_warning: Mapped[bool] = mapped_column(Boolean, default=True, comment="3-day expiry warning")
    new_predicted_paper: Mapped[bool] = mapped_column(Boolean, default=True, comment="New predicted paper published")
    weekly_current_affairs: Mapped[bool] = mapped_column(Boolean, default=True, comment="Monday weekly digest")
    password_reset: Mapped[bool] = mapped_column(Boolean, default=True, comment="Password reset (always sent, but tracked)")
    marketing: Mapped[bool] = mapped_column(Boolean, default=True, comment="Promotional / upgrade nudges")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_email_preferences_user"),
    )

    def __repr__(self) -> str:
        return f"<EmailPreference user_id={self.user_id}>"
