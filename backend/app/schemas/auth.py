"""Auth schemas — Supabase-integrated request/response models."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ═══════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    phone: str | None = None


class RegisterResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    message: str = "Account created successfully. Check your email for confirmation."


# ═══════════════════════════════════════════════════════════
# Login (email/password)
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseModel):
    """Returned on successful login/refresh.  Refresh token is in httpOnly cookie."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until access token expires")
    user: "AuthUserInfo"


class AuthUserInfo(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    avatar_url: str | None = None
    auth_provider: str = "email"
    is_premium: bool = False
    subscription_tier: str = "free"

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Magic Link
# ═══════════════════════════════════════════════════════════

class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkResponse(BaseModel):
    message: str = "Magic link sent. Check your email."


# ═══════════════════════════════════════════════════════════
# Google OAuth
# ═══════════════════════════════════════════════════════════

class OAuthURLResponse(BaseModel):
    """Redirect the frontend to this URL to start Google OAuth."""
    url: str
    provider: str = "google"


class OAuthCallbackRequest(BaseModel):
    """The frontend sends the Supabase session tokens after OAuth redirect."""
    access_token: str
    refresh_token: str


# ═══════════════════════════════════════════════════════════
# Token / Refresh
# ═══════════════════════════════════════════════════════════

class TokenPayload(BaseModel):
    sub: str        # user UUID as string
    exp: int
    type: str       # "access" | "refresh"


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ═══════════════════════════════════════════════════════════
# Forgot / Reset Password
# ═══════════════════════════════════════════════════════════

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str = "Password reset email sent. Check your inbox."


class ResetPasswordRequest(BaseModel):
    access_token: str = Field(..., description="Token from the reset email link")
    new_password: str = Field(..., min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    message: str = "Password updated successfully."


# ═══════════════════════════════════════════════════════════
# Profile Update (PUT /auth/me)
# ═══════════════════════════════════════════════════════════

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    selected_job_types: list[UUID] | None = None


class UpdateProfileResponse(BaseModel):
    message: str = "Profile updated."
    user: AuthUserInfo
