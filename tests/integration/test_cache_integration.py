"""Integration tests for Redis cache with weather service."""

import respx
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient

from weather_api.config import settings
from weather_api.main import app
from weather_api.services import cache as cache_module
from weather_api.services.cache import (
    get_coordinates_cache_key,
    get_weather_cache_key,
)
from weather_api.services.weather import GEOCODING_URL, WEATHER_URL

from ..conftest import mock_geocoding_response, mock_weather_response


class TestCacheIntegration:
    """Tests for cache integration with weather service."""

    @respx.mock
    async def test_coordinates_cached_on_first_request(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """First request should populate the coordinates cache."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 200

            # Verify coordinates were cached
            cache_key = get_coordinates_cache_key("London")
            cached_value = await fake_redis.get(cache_key)
            assert cached_value is not None
            assert "51.5074" in cached_value
            assert "-0.1278" in cached_value
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_second_request_uses_cached_coordinates(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Second request should use cached coordinates and skip geocoding API."""
        geocoding_route = respx.get(GEOCODING_URL).mock(
            return_value=mock_geocoding_response()
        )
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # First request
                response1 = await client.get("/forecast/London")
                assert response1.status_code == 200

                # Second request
                response2 = await client.get("/forecast/London")
                assert response2.status_code == 200

            # Geocoding should only be called once
            assert geocoding_route.call_count == 1
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_cache_key_case_insensitive(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Cache keys should be case-insensitive (LONDON and london share cache)."""
        geocoding_route = respx.get(GEOCODING_URL).mock(
            return_value=mock_geocoding_response()
        )
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # Request with lowercase
                response1 = await client.get("/forecast/london")
                assert response1.status_code == 200

                # Request with uppercase - should use cache
                response2 = await client.get("/forecast/LONDON")
                assert response2.status_code == 200

            # Geocoding should only be called once due to case-insensitive cache
            assert geocoding_route.call_count == 1
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_weather_cached_after_fetch(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Weather data should be cached with correct TTL after fetch."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 200

            # Verify weather was cached
            cache_key = get_weather_cache_key(51.5074, -0.1278)
            cached_value = await fake_redis.get(cache_key)
            assert cached_value is not None
            assert "15.5" in cached_value  # temperature

            # Verify TTL was set (should be around cache_weather_ttl)
            ttl = await fake_redis.ttl(cache_key)
            assert ttl > 0
            assert ttl <= settings.cache_weather_ttl
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_cached_weather_used_on_repeat_request(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Both caches hit means no API calls on repeat request."""
        geocoding_route = respx.get(GEOCODING_URL).mock(
            return_value=mock_geocoding_response()
        )
        weather_route = respx.get(WEATHER_URL).mock(
            return_value=mock_weather_response()
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # First request - populates both caches
                response1 = await client.get("/forecast/London")
                assert response1.status_code == 200
                assert geocoding_route.call_count == 1
                assert weather_route.call_count == 1

                # Second request - should use both caches
                response2 = await client.get("/forecast/London")
                assert response2.status_code == 200

            # No additional API calls
            assert geocoding_route.call_count == 1
            assert weather_route.call_count == 1
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_requests_work_without_cache(self) -> None:
        """API should work when Redis is unavailable."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        # Ensure no Redis client
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
    async def test_different_cities_have_separate_cache_entries(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Different cities should have separate cache entries."""
        respx.get(GEOCODING_URL).mock(
            side_effect=[
                mock_geocoding_response("London", 51.5074, -0.1278),
                mock_geocoding_response("Paris", 48.8566, 2.3522),
            ]
        )
        respx.get(WEATHER_URL).mock(
            side_effect=[
                mock_weather_response(temperature=15.5),
                mock_weather_response(temperature=18.0),
            ]
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response1 = await client.get("/forecast/London")
                response2 = await client.get("/forecast/Paris")

            assert response1.status_code == 200
            assert response2.status_code == 200

            # Verify separate cache entries
            london_key = get_coordinates_cache_key("London")
            paris_key = get_coordinates_cache_key("Paris")

            london_cached = await fake_redis.get(london_key)
            paris_cached = await fake_redis.get(paris_key)

            assert london_cached is not None
            assert paris_cached is not None
            assert london_cached != paris_cached
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_partial_cache_hit_coordinates_only(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """When only coordinates are cached, weather API should still be called."""
        geocoding_route = respx.get(GEOCODING_URL).mock(
            return_value=mock_geocoding_response()
        )
        weather_route = respx.get(WEATHER_URL).mock(
            return_value=mock_weather_response()
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            # Pre-populate only coordinates cache
            coords_key = get_coordinates_cache_key("London")
            await fake_redis.set(
                coords_key,
                '{"latitude": 51.5074, "longitude": -0.1278}',
            )

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/forecast/London")

            assert response.status_code == 200

            # Geocoding should NOT be called (cache hit)
            assert geocoding_route.call_count == 0
            # Weather should be called (cache miss)
            assert weather_route.call_count == 1
        finally:
            cache_module._redis_client = original_client
