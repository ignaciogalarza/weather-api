"""Application configuration with validation."""

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

    # Redis cache
    redis_url: str | None = None  # e.g., "redis://localhost:6379"
    redis_password: str | None = None
    cache_enabled: bool = True
    cache_coordinates_ttl: int = 2592000  # 30 days in seconds
    cache_weather_ttl: int = 900  # 15 minutes in seconds

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
