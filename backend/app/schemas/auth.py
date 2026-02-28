"""Auth schemas — login / register / token."""

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    job_type: str | None = None


class RegisterResponse(BaseModel):
    id: int
    email: str
    full_name: str
    message: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str  # "access" | "refresh"
