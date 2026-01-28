"""Shared fixtures for integration tests."""

from collections.abc import AsyncIterator, Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import jwt
import pytest
import respx
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient, Response

from weather_api.main import app
from weather_api.ratelimit import limiter
from weather_api.services import cache as cache_module
from weather_api.services.weather import GEOCODING_URL, WEATHER_URL

# Test constants
TEST_JWT_SECRET = "test-secret-key-for-testing"  # noqa: S105
TEST_JWT_ALGORITHM = "HS256"
TEST_API_KEY = "test-api-key-12345"


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Generator[None, None, None]:
    """Reset rate limiter state before each test to avoid cross-test pollution."""
    # Clear rate limiter storage before each test
    if hasattr(limiter, "_storage"):
        limiter._storage.reset()
    yield


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def fake_redis() -> FakeAsyncRedis:
    """Create a fake Redis instance for testing."""
    return FakeAsyncRedis(decode_responses=True)


@pytest.fixture
async def app_with_cache(fake_redis: FakeAsyncRedis) -> AsyncIterator[FakeAsyncRedis]:
    """Inject fake Redis into the cache module."""
    original_client = cache_module._redis_client
    cache_module._redis_client = fake_redis  # type: ignore[assignment]
    try:
        yield fake_redis
    finally:
        cache_module._redis_client = original_client


@pytest.fixture
def auth_headers_api_key() -> dict[str, str]:
    """Pre-configured API key headers."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def create_test_token() -> Callable[[str, bool], str]:
    """Factory to create JWT tokens for testing."""

    def _create_token(username: str, expired: bool = False) -> str:
        if expired:
            exp = datetime.now(UTC) - timedelta(hours=1)
        else:
            exp = datetime.now(UTC) + timedelta(hours=1)
        payload = {"sub": username, "exp": exp}
        return jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)

    return _create_token


@pytest.fixture
def auth_headers_jwt(create_test_token: Callable[[str, bool], str]) -> dict[str, str]:
    """Pre-configured JWT headers."""
    token = create_test_token("testuser", expired=False)
    return {"Authorization": f"Bearer {token}"}


def mock_geocoding_response(
    city: str = "London",
    latitude: float = 51.5074,
    longitude: float = -0.1278,
) -> Response:
    """Create a mock geocoding API response."""
    return Response(
        200,
        json={
            "results": [
                {
                    "name": city,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            ]
        },
    )


def mock_weather_response(
    temperature: float = 15.5,
    humidity: int = 72,
    wind_speed: float = 12.3,
    weather_code: int = 2,
) -> Response:
    """Create a mock weather API response."""
    return Response(
        200,
        json={
            "current": {
                "temperature_2m": temperature,
                "relative_humidity_2m": humidity,
                "wind_speed_10m": wind_speed,
                "weather_code": weather_code,
            }
        },
    )


@pytest.fixture
def mock_external_apis() -> Callable[[], None]:
    """Factory for setting up respx mocks for external APIs."""

    def _setup_mocks(
        geocoding_response: Response | None = None,
        weather_response: Response | None = None,
    ) -> None:
        if geocoding_response is None:
            geocoding_response = mock_geocoding_response()
        if weather_response is None:
            weather_response = mock_weather_response()

        respx.get(GEOCODING_URL).mock(return_value=geocoding_response)
        respx.get(WEATHER_URL).mock(return_value=weather_response)

    return _setup_mocks


@pytest.fixture
def mock_auth_settings() -> Any:
    """Context manager to mock authentication settings."""

    class AuthSettingsMocker:
        def __init__(self) -> None:
            self._patches: list[Any] = []

        def enable_api_key(
            self, api_keys: set[str] | None = None
        ) -> "AuthSettingsMocker":
            if api_keys is None:
                api_keys = {TEST_API_KEY}
            self._api_key_enabled = True
            self._api_keys = api_keys
            return self

        def enable_jwt(self) -> "AuthSettingsMocker":
            self._jwt_enabled = True
            return self

        def disable_all(self) -> "AuthSettingsMocker":
            self._api_key_enabled = False
            self._jwt_enabled = False
            return self

        def __enter__(self) -> "AuthSettingsMocker":
            auth_patch = patch("weather_api.auth.settings")
            mock_settings = auth_patch.start()
            self._patches.append(auth_patch)

            mock_settings.api_key_enabled = getattr(self, "_api_key_enabled", False)
            mock_settings.jwt_enabled = getattr(self, "_jwt_enabled", False)
            mock_settings.api_keys = getattr(self, "_api_keys", set())
            mock_settings.jwt_secret = TEST_JWT_SECRET
            mock_settings.jwt_algorithm = TEST_JWT_ALGORITHM

            return self

        def __exit__(self, *args: object) -> None:
            for p in self._patches:
                p.stop()

    return AuthSettingsMocker()
