"""Email preference schemas — manage per-user email opt-in/out."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EmailPreferenceBase(BaseModel):
    welcome: bool = True
    subscription_confirmation: bool = True
    subscription_expiry_warning: bool = True
    new_predicted_paper: bool = True
    weekly_current_affairs: bool = True
    password_reset: bool = True
    marketing: bool = True


class EmailPreferenceUpdate(BaseModel):
    """Partial update — only provided fields are changed."""
    welcome: bool | None = None
    subscription_confirmation: bool | None = None
    subscription_expiry_warning: bool | None = None
    new_predicted_paper: bool | None = None
    weekly_current_affairs: bool | None = None
    password_reset: bool | None = None
    marketing: bool | None = None


class EmailPreferenceResponse(EmailPreferenceBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class EmailLogResponse(BaseModel):
    """Single email log entry."""
    id: UUID
    user_id: UUID | None = None
    to_email: str
    email_type: str
    subject: str
    resend_id: str | None = None
    status: str
    sent_at: datetime

    model_config = {"from_attributes": True}


class EmailLogListResponse(BaseModel):
    items: list[EmailLogResponse]
    total: int
