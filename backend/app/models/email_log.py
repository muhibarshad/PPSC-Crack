"""
Email Log model — tracks every email sent for auditing and rate-limiting.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    to_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="welcome | subscription_confirmation | subscription_expiry_warning | "
                "new_predicted_paper | weekly_current_affairs | password_reset",
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    resend_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Resend API message ID"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="sent", comment="sent | failed | bounced"
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<EmailLog id={self.id} type={self.email_type} to={self.to_email}>"
