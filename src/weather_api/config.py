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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
