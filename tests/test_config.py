"""Tests for application configuration."""

import os
from unittest.mock import patch

from weather_api.config import Settings


class TestSettings:
    """Test Settings configuration class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        settings = Settings()
        assert settings.log_format == "json"
        assert settings.log_level == "INFO"
        assert settings.otel_exporter_otlp_endpoint is None
        assert settings.otel_console_export is False
        assert settings.service_name == "weather-api"
        assert settings.service_version == "0.1.0"

    def test_environment_override(self) -> None:
        """Test configuration can be overridden via environment variables."""
        with patch.dict(
            os.environ,
            {
                "LOG_FORMAT": "console",
                "LOG_LEVEL": "DEBUG",
                "OTEL_EXPORTER_OTLP_ENDPOINT": "http://tempo:4317",
                "OTEL_CONSOLE_EXPORT": "true",
            },
        ):
            settings = Settings()
            assert settings.log_format == "console"
            assert settings.log_level == "DEBUG"
            assert settings.otel_exporter_otlp_endpoint == "http://tempo:4317"
            assert settings.otel_console_export is True
