"""
PPSC Crack — Auth Endpoints (Supabase Integration)
=====================================================
POST /register          — email + password sign-up
POST /login             — email + password sign-in
POST /magic-link        — passwordless magic-link
GET  /oauth/google      — initiate Google OAuth flow
POST /oauth/callback    — exchange Supabase OAuth session
POST /refresh           — rotate refresh token (httpOnly cookie)
POST /logout            — clear session + cookie
GET  /me                — current user profile
PUT  /me                — update profile
POST /forgot-password   — request password-reset email
POST /reset-password    — set new password via reset token
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

try:
    from supabase_auth.errors import AuthApiError
except ImportError:
    from gotrue.errors import AuthApiError  # fallback for older installs

from app.config import settings
from app.core.rate_limiter import auth_rate_limit
from app.core.security import (
    clear_refresh_cookie,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    set_refresh_cookie,
    REFRESH_COOKIE_NAME,
)
from app.core.supabase_client import get_supabase, get_supabase_admin
from app.crud import crud_user
from app.dependencies import DBSession, get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthTokenResponse,
    AuthUserInfo,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    MagicLinkRequest,
    MagicLinkResponse,
    OAuthCallbackRequest,
    OAuthURLResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    UpdateProfileRequest,
    UpdateProfileResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ─────────────────────────────────────────────────

def _user_info(user: User) -> AuthUserInfo:
    """Build an ``AuthUserInfo`` payload from a local User model."""
    return AuthUserInfo.model_validate(user, from_attributes=True)


def _build_token_response(
    user: User, access_token: str, expires_in: int | None = None,
) -> AuthTokenResponse:
    return AuthTokenResponse(
        access_token=access_token,
        expires_in=expires_in or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_info(user),
    )


# ═══════════════════════════════════════════════════════════
# POST /register
# ═══════════════════════════════════════════════════════════

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: DBSession,
    _rate: None = Depends(auth_rate_limit),
):
    """Register a new user via Supabase email+password sign-up."""

    # 1 — Check for existing local user
    existing = await crud_user.get_by_email(db, email=body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # 2 — Sign up in Supabase
    sb = get_supabase()
    try:
        res = sb.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {
                "data": {
                    "name": body.name,
                    "phone": body.phone,
                },
            },
        })
    except AuthApiError as exc:
        logger.warning("Supabase sign-up error: %s", exc.message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    sb_user = res.user
    if sb_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase sign-up did not return a user.",
        )

    # 3 — Create local user row
    from app.schemas.user import UserCreate

    user = await crud_user.create(
        db,
        obj_in=UserCreate(
            email=body.email,
            name=body.name,
            phone=body.phone,
            password=body.password,
            supabase_uid=sb_user.id,
            auth_provider="email",
        ),
    )
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
    )


# ═══════════════════════════════════════════════════════════
# POST /login
# ═══════════════════════════════════════════════════════════

@router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: DBSession,
    _rate: None = Depends(auth_rate_limit),
):
    """Authenticate with email + password via Supabase.

    Returns a Supabase access token in the body and sets the
    refresh token in an httpOnly cookie.
    """
    sb = get_supabase()
    try:
        res = sb.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
    except AuthApiError as exc:
        logger.warning("Login failed for %s: %s", body.email, exc.message)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    session = res.session
    sb_user = res.user
    if session is None or sb_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
        )

    # Ensure local user exists
    user, _ = await crud_user.get_or_create_from_supabase(
        db,
        supabase_uid=sb_user.id,
        email=sb_user.email or body.email,
        name=(
            (sb_user.user_metadata or {}).get("name")
            or body.email.split("@")[0]
        ),
        auth_provider="email",
    )
    await db.commit()
    await db.refresh(user)

    # Set httpOnly refresh cookie
    set_refresh_cookie(response, session.refresh_token)

    return _build_token_response(
        user=user,
        access_token=session.access_token,
        expires_in=session.expires_in,
    )


# ═══════════════════════════════════════════════════════════
# POST /magic-link
# ═══════════════════════════════════════════════════════════

@router.post("/magic-link", response_model=MagicLinkResponse)
async def send_magic_link(
    body: MagicLinkRequest,
    _rate: None = Depends(auth_rate_limit),
):
    """Send a passwordless magic-link email via Supabase."""
    sb = get_supabase()
    try:
        sb.auth.sign_in_with_otp({
            "email": body.email,
            "options": {"should_create_user": True},
        })
    except AuthApiError as exc:
        logger.warning("Magic link error for %s: %s", body.email, exc.message)
        # Don't reveal whether the email exists
    return MagicLinkResponse()


# ═══════════════════════════════════════════════════════════
# GET /oauth/google
# ═══════════════════════════════════════════════════════════

@router.get("/oauth/google", response_model=OAuthURLResponse)
async def google_oauth_url(
    _rate: None = Depends(auth_rate_limit),
):
    """Return the Supabase OAuth redirect URL for Google sign-in."""
    sb = get_supabase()
    try:
        res = sb.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": f"{settings.SUPABASE_URL}/auth/v1/callback",
            },
        })
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OAuth init failed: {exc.message}",
        )
    return OAuthURLResponse(url=res.url, provider="google")


# ═══════════════════════════════════════════════════════════
# POST /oauth/callback
# ═══════════════════════════════════════════════════════════

@router.post("/oauth/callback", response_model=AuthTokenResponse)
async def oauth_callback(
    body: OAuthCallbackRequest,
    response: Response,
    db: DBSession,
    _rate: None = Depends(auth_rate_limit),
):
    """Exchange Supabase OAuth tokens for a local session.

    The frontend obtains ``access_token`` and ``refresh_token`` from the
    Supabase redirect, then sends them here to link / create the local user.
    """
    from app.core.security import verify_supabase_token

    try:
        payload = verify_supabase_token(body.access_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OAuth access token.",
        )

    supabase_uid = payload.get("sub", "")
    email = payload.get("email", "")
    meta = payload.get("user_metadata", {})
    name = meta.get("full_name") or meta.get("name") or email.split("@")[0]
    avatar = meta.get("avatar_url")
    provider = payload.get("app_metadata", {}).get("provider", "google")

    user, _ = await crud_user.get_or_create_from_supabase(
        db,
        supabase_uid=supabase_uid,
        email=email,
        name=name,
        avatar_url=avatar,
        auth_provider=provider,
    )
    await db.commit()
    await db.refresh(user)

    set_refresh_cookie(response, body.refresh_token)

    return _build_token_response(
        user=user,
        access_token=body.access_token,
    )


# ═══════════════════════════════════════════════════════════
# POST /refresh
# ═══════════════════════════════════════════════════════════

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: DBSession,
    _rate: None = Depends(auth_rate_limit),
):
    """Rotate the refresh token and return a new access token.

    The refresh token is read from the httpOnly cookie.  On success the
    old cookie is replaced with the new refresh token (rotation).
    """
    old_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if not old_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie.",
        )

    # Try Supabase session refresh first
    sb = get_supabase()
    try:
        res = sb.auth.refresh_session(old_refresh)
        session = res.session
        if session is None:
            raise AuthApiError("No session returned", 401)
    except (AuthApiError, Exception) as exc:
        # Fallback: try as an internal refresh token
        try:
            payload = decode_token(old_refresh)
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type.",
                )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload.",
                )
            new_access = create_access_token(data={"sub": user_id})
            new_refresh = create_refresh_token(data={"sub": user_id})
            set_refresh_cookie(response, new_refresh)
            return RefreshResponse(
                access_token=new_access,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )
        except Exception:
            clear_refresh_cookie(response)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or expired.",
            )

    # Supabase refresh succeeded — rotate cookie
    set_refresh_cookie(response, session.refresh_token)
    return RefreshResponse(
        access_token=session.access_token,
        expires_in=session.expires_in or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ═══════════════════════════════════════════════════════════
# POST /logout
# ═══════════════════════════════════════════════════════════

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
):
    """Sign out: clear refresh cookie and invalidate Supabase session."""
    # Best-effort Supabase sign-out
    try:
        sb = get_supabase()
        sb.auth.sign_out()
    except Exception:
        pass  # Non-critical

    clear_refresh_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════
# GET /me
# ═══════════════════════════════════════════════════════════

@router.get("/me", response_model=AuthUserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return _user_info(current_user)


# ═══════════════════════════════════════════════════════════
# PUT /me
# ═══════════════════════════════════════════════════════════

@router.put("/me", response_model=UpdateProfileResponse)
async def update_me(
    body: UpdateProfileRequest,
    db: DBSession,
    current_user: User = Depends(get_current_user),
):
    """Update the current user's profile fields."""
    from app.schemas.user import UserUpdate

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    updated = await crud_user.update(
        db,
        db_obj=current_user,
        obj_in=UserUpdate(**update_data),
    )
    await db.commit()
    await db.refresh(updated)

    return UpdateProfileResponse(user=_user_info(updated))


# ═══════════════════════════════════════════════════════════
# POST /forgot-password
# ═══════════════════════════════════════════════════════════

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    body: ForgotPasswordRequest,
    _rate: None = Depends(auth_rate_limit),
):
    """Send a password-reset email via Supabase."""
    sb = get_supabase()
    try:
        sb.auth.reset_password_email(body.email)
    except AuthApiError as exc:
        logger.warning("Password reset error for %s: %s", body.email, exc.message)
        # Don't reveal whether the email exists
    return ForgotPasswordResponse()


# ═══════════════════════════════════════════════════════════
# POST /reset-password
# ═══════════════════════════════════════════════════════════

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    body: ResetPasswordRequest,
    _rate: None = Depends(auth_rate_limit),
):
    """Set a new password using the token from the reset email.

    The ``access_token`` is the one Supabase puts in the email link.
    We use the admin client to update the password server-side.
    """
    from app.core.security import verify_supabase_token

    try:
        payload = verify_supabase_token(body.access_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token.",
        )

    supabase_uid = payload.get("sub")
    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing user identifier.",
        )

    admin_sb = get_supabase_admin()
    try:
        admin_sb.auth.admin.update_user_by_id(
            supabase_uid,
            {"password": body.new_password},
        )
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    return ResetPasswordResponse()
