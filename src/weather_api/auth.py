"""API key and JWT authentication."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from weather_api.config import settings

# Security schemes
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_SCHEME = HTTPBearer(auto_error=False)

# Module-level Security dependencies (avoids B008 warning)
_API_KEY_SECURITY = Security(API_KEY_HEADER)
_BEARER_SECURITY = Security(BEARER_SCHEME)


def create_access_token(username: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_expiration_minutes
    )
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


async def validate_api_key(
    api_key: str | None = _API_KEY_SECURITY,
) -> str | None:
    """Validate API key from request header.

    Returns the API key if valid, or None if auth is disabled.
    Raises HTTPException 401/403 if invalid.
    """
    if not settings.api_key_enabled:
        return None

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    if api_key not in settings.api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


async def validate_auth(
    bearer: HTTPAuthorizationCredentials | None = _BEARER_SECURITY,
    api_key: str | None = _API_KEY_SECURITY,
) -> str | None:
    """Validate authentication - JWT or API key.

    Returns username (JWT) or API key string if valid.
    Returns None if all auth is disabled.
    Raises HTTPException 401/403 if invalid.
    """
    # Try JWT first if enabled and token provided
    if settings.jwt_enabled and bearer:
        try:
            payload = jwt.decode(
                bearer.credentials,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            sub: str | None = payload.get("sub")
            return sub
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired") from None
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token") from None

    # Try API key if enabled and provided
    if settings.api_key_enabled and api_key:
        if api_key not in settings.api_keys:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return api_key

    # No auth required if both are disabled
    if not settings.jwt_enabled and not settings.api_key_enabled:
        return None

    # Auth required but not provided
    raise HTTPException(status_code=401, detail="Missing authentication")
