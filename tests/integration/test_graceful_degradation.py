"""Integration tests for graceful degradation under failure conditions."""

from unittest.mock import AsyncMock

import httpx
import respx
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient, Response
from redis.exceptions import RedisError

from weather_api.main import app
from weather_api.services import cache as cache_module
from weather_api.services.cache import get_coordinates_cache_key
from weather_api.services.weather import GEOCODING_URL, WEATHER_URL

from ..conftest import mock_geocoding_response, mock_weather_response


class TestGracefulDegradation:
    """Tests for system behavior under failure conditions."""

    @respx.mock
    async def test_api_works_when_redis_unavailable(self) -> None:
        """API should work when Redis is not configured."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 200
            data = response.json()
            assert data["city"] == "London"
            assert data["temperature"] == 15.5
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_redis_error_during_get_continues_to_api(self) -> None:
        """When cache read fails, request should continue to external API."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        # Create a mock that raises on get
        mock_redis = AsyncMock()
        mock_redis.get.side_effect = RedisError("Connection lost")

        original_client = cache_module._redis_client
        cache_module._redis_client = mock_redis

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            # Should succeed via API fallback
            assert response.status_code == 200
            data = response.json()
            assert data["city"] == "London"
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_redis_error_during_set_does_not_fail_request(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """When cache write fails, request should still succeed."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        # Create a mock that works for get but fails for set
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None  # Cache miss
        mock_redis.set.side_effect = RedisError("Connection lost")

        original_client = cache_module._redis_client
        cache_module._redis_client = mock_redis

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            # Should succeed even though cache write failed
            assert response.status_code == 200
            data = response.json()
            assert data["city"] == "London"
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_geocoding_timeout_returns_503(self) -> None:
        """Geocoding API timeout should return 503."""
        respx.get(GEOCODING_URL).mock(side_effect=httpx.TimeoutException("Timeout"))

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 503
            assert "Geocoding request failed" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_weather_api_timeout_returns_503(self) -> None:
        """Weather API timeout should return 503."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(side_effect=httpx.TimeoutException("Timeout"))

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 503
            assert "Weather request failed" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_geocoding_500_error_returns_503(self) -> None:
        """External API 500 error should return our 503."""
        respx.get(GEOCODING_URL).mock(return_value=Response(500))

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 503
            assert "Geocoding API error: 500" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_weather_api_500_error_returns_503(self) -> None:
        """Weather API 500 error should return our 503."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=Response(500))

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 503
            assert "Weather API error: 500" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_coords_cached_but_weather_api_fails(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """When coordinates are cached but weather API fails, return 503."""
        geocoding_route = respx.get(GEOCODING_URL).mock(
            return_value=mock_geocoding_response()
        )
        respx.get(WEATHER_URL).mock(return_value=Response(503))

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            # Pre-populate coordinates cache
            coords_key = get_coordinates_cache_key("London")
            await fake_redis.set(
                coords_key,
                '{"latitude": 51.5074, "longitude": -0.1278}',
            )

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            # Should fail with 503
            assert response.status_code == 503

            # Geocoding should not be called (cache hit)
            assert geocoding_route.call_count == 0
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_request_error_during_geocoding(self) -> None:
        """Network error during geocoding should return 503."""
        respx.get(GEOCODING_URL).mock(
            side_effect=httpx.RequestError("Connection refused")
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 503
            assert "Geocoding request failed" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_request_error_during_weather_fetch(self) -> None:
        """Network error during weather fetch should return 503."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(
            side_effect=httpx.RequestError("Connection refused")
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 503
            assert "Weather request failed" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client
