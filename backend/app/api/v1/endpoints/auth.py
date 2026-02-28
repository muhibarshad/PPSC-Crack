"""
Auth endpoints — register, login, refresh, me.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import DBSession, get_current_user
from app.schemas.auth import TokenResponse, RegisterRequest, RegisterResponse
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: DBSession):
    """Create a new user account."""
    # TODO: Check if email already exists
    # TODO: Create user in DB
    hashed = hash_password(body.password)
    return RegisterResponse(
        id=1,
        email=body.email,
        full_name=body.full_name,
        message="Account created successfully",
    )


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: DBSession = None):  # type: ignore[assignment]
    """Authenticate and return JWT tokens."""
    # TODO: Fetch user by email, verify password
    # Placeholder — always succeeds for scaffolding
    access_token = create_access_token(data={"sub": "1"})
    refresh_token = create_refresh_token(data={"sub": "1"})
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/me")
async def read_current_user(current_user=Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user
