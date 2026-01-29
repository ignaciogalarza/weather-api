"""Application configuration with validation."""

from pydantic import field_validator
from pydantic_settings import BaseSettings

from weather_api import __version__


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    For example, LOG_LEVEL=DEBUG will set log_level to "DEBUG".
    """

    # Logging
    log_format: str = "json"
    log_level: str = "INFO"

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str | None = None
    otel_console_export: bool = False

    # Service info
    service_name: str = "weather-api"
    service_version: str = __version__

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_forecast: str = "30/minute"
    rate_limit_storage: str = "memory"  # "memory" or "redis"

    # API Key Authentication
    api_key_enabled: bool = False  # Disabled by default for dev
    api_keys: set[str] = set()  # Comma-separated in env: API_KEYS="key1,key2"

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v: str | set[str]) -> set[str]:
        """Parse comma-separated API keys from environment variable."""
        if isinstance(v, str):
            return {k.strip() for k in v.split(",") if k.strip()}
        return v

    # JWT Authentication
    jwt_enabled: bool = False  # Disabled by default for dev
    jwt_secret: str = "change-me-in-production"  # noqa: S105
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    jwt_users: dict[str, str] = {}  # Format: "user1:hash1,user2:hash2"

    @field_validator("jwt_users", mode="before")
    @classmethod
    def parse_jwt_users(cls, v: str | dict[str, str]) -> dict[str, str]:
        """Parse comma-separated user:hash pairs from environment variable."""
        if isinstance(v, str):
            users: dict[str, str] = {}
            for pair in v.split(","):
                if ":" in pair:
                    username, password_hash = pair.strip().split(":", 1)
                    users[username.strip()] = password_hash.strip()
            return users
        return v

    # Redis cache
    redis_url: str | None = None  # e.g., "redis://localhost:6379"
    redis_password: str | None = None
    cache_enabled: bool = True
    cache_coordinates_ttl: int = 2592000  # 30 days in seconds
    cache_weather_ttl: int = 900  # 15 minutes in seconds

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
