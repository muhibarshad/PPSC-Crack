"""User schemas — aligned with the Supabase-aware User model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════
# Base / Shared
# ═══════════════════════════════════════════════════════════

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = None
    avatar_url: str | None = None


# ═══════════════════════════════════════════════════════════
# Create — password optional (Supabase handles auth)
# ═══════════════════════════════════════════════════════════

class UserCreate(UserBase):
    password: str | None = Field(None, min_length=8, max_length=128)
    supabase_uid: str | None = None
    auth_provider: str = "email"
    role: str = "student"


# ═══════════════════════════════════════════════════════════
# Update
# ═══════════════════════════════════════════════════════════

class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    role: str | None = None
    is_premium: bool | None = None
    subscription_tier: str | None = None


# ═══════════════════════════════════════════════════════════
# Read / Response
# ═══════════════════════════════════════════════════════════

class UserResponse(UserBase):
    id: UUID
    supabase_uid: str | None = None
    role: str
    auth_provider: str
    is_premium: bool
    subscription_tier: str
    selected_job_types: list[UUID] | None = None
    learning_progress: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    """Lightweight user reference for nested responses."""
    id: UUID
    email: str
    name: str
    role: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Admin views
# ═══════════════════════════════════════════════════════════

class UserAdminResponse(UserResponse):
    """Includes sensitive fields only admins should see."""
    last_login_at: datetime | None = None
