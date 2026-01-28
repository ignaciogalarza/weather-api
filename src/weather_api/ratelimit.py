"""Rate limiting configuration using SlowAPI."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from weather_api.config import settings


def _get_key_func(request: Request) -> str:
    """Get rate limit key from request."""
    return get_remote_address(request) or "unknown"


def _create_limiter() -> Limiter:
    """Create and configure the rate limiter."""
    if not settings.rate_limit_enabled:
        # Return a limiter that is effectively disabled
        return Limiter(
            key_func=_get_key_func,
            enabled=False,
        )

    storage_uri: str | None = None
    if settings.rate_limit_storage == "redis":
        # Import here to avoid circular imports
        redis_url = getattr(settings, "redis_url", None)
        if redis_url:
            storage_uri = redis_url

    return Limiter(
        key_func=_get_key_func,
        default_limits=[settings.rate_limit_default],
        storage_uri=storage_uri,
        enabled=True,
    )


limiter = _create_limiter()
