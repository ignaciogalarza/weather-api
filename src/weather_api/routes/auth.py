"""Authentication routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from weather_api.auth import create_access_token, verify_password
from weather_api.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login credentials."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get JWT token",
    description="Authenticate with username and password to receive a JWT token.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        503: {"description": "JWT authentication not enabled"},
    },
)
async def login(credentials: LoginRequest) -> TokenResponse:
    """Authenticate with username/password and receive a JWT token."""
    if not settings.jwt_enabled:
        raise HTTPException(status_code=503, detail="JWT authentication not enabled")

    password_hash = settings.jwt_users.get(credentials.username)
    if not password_hash or not verify_password(credentials.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(credentials.username)
    return TokenResponse(access_token=access_token)
