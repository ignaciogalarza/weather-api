"""End-to-end integration tests for complete request flows."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jwt
import respx
from fakeredis import FakeAsyncRedis
from httpx import ASGITransport, AsyncClient, Response

from weather_api.main import app
from weather_api.services import cache as cache_module
from weather_api.services.cache import (
    get_coordinates_cache_key,
    get_weather_cache_key,
)
from weather_api.services.weather import GEOCODING_URL, WEATHER_URL

from ..conftest import (
    TEST_API_KEY,
    TEST_JWT_ALGORITHM,
    TEST_JWT_SECRET,
    mock_geocoding_response,
    mock_weather_response,
)


class TestEndToEndFlows:
    """Tests for complete request flows through all layers."""

    @respx.mock
    async def test_authenticated_cached_request_flow(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Test Auth → Cache Hit → Response flow."""
        geocoding_route = respx.get(GEOCODING_URL).mock(
            return_value=mock_geocoding_response()
        )
        weather_route = respx.get(WEATHER_URL).mock(
            return_value=mock_weather_response()
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = True
                mock_settings.jwt_enabled = False
                mock_settings.api_keys = {TEST_API_KEY}

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    # First request - populates cache
                    response1 = await client.get(
                        "/forecast/London",
                        headers={"X-API-Key": TEST_API_KEY},
                    )
                    assert response1.status_code == 200
                    assert geocoding_route.call_count == 1
                    assert weather_route.call_count == 1

                    # Second request - should use cache
                    response2 = await client.get(
                        "/forecast/London",
                        headers={"X-API-Key": TEST_API_KEY},
                    )
                    assert response2.status_code == 200

                    # No additional API calls (cache hit)
                    assert geocoding_route.call_count == 1
                    assert weather_route.call_count == 1

                    # Response data should match
                    assert response1.json() == response2.json()
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_authenticated_uncached_request_flow(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Test Auth → APIs → Cache Write → Response flow."""
        geocoding_route = respx.get(GEOCODING_URL).mock(
            return_value=mock_geocoding_response()
        )
        weather_route = respx.get(WEATHER_URL).mock(
            return_value=mock_weather_response()
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = True
                mock_settings.jwt_enabled = False
                mock_settings.api_keys = {TEST_API_KEY}

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get(
                        "/forecast/London",
                        headers={"X-API-Key": TEST_API_KEY},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["city"] == "London"
                assert data["temperature"] == 15.5
                assert data["humidity"] == 72
                assert data["wind_speed"] == 12.3
                assert data["conditions"] == "Partly cloudy"

                # Verify both APIs were called
                assert geocoding_route.call_count == 1
                assert weather_route.call_count == 1

                # Verify cache was populated
                coords_key = get_coordinates_cache_key("London")
                weather_key = get_weather_cache_key(51.5074, -0.1278)

                assert await fake_redis.exists(coords_key)
                assert await fake_redis.exists(weather_key)
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_jwt_authenticated_request_flow(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Test full JWT authentication flow."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            # Create a valid JWT token
            payload = {
                "sub": "testuser",
                "exp": datetime.now(UTC) + timedelta(hours=1),
            }
            token = jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)

            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = False
                mock_settings.jwt_enabled = True
                mock_settings.jwt_secret = TEST_JWT_SECRET
                mock_settings.jwt_algorithm = TEST_JWT_ALGORITHM

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get(
                        "/forecast/London",
                        headers={"Authorization": f"Bearer {token}"},
                    )

                assert response.status_code == 200
                data = response.json()
                assert data["city"] == "London"
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_city_not_found_flow(self) -> None:
        """Test 404 error propagation for unknown city."""
        respx.get(GEOCODING_URL).mock(
            return_value=Response(200, json={"results": []})
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = False
                mock_settings.jwt_enabled = False

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/forecast/UnknownCity123")

                assert response.status_code == 404
                assert "City not found" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_external_api_failure_flow(self) -> None:
        """Test 503 error propagation for external API failure."""
        respx.get(GEOCODING_URL).mock(return_value=Response(500))

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = False
                mock_settings.jwt_enabled = False

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/forecast/London")

                assert response.status_code == 503
                assert "Geocoding API error" in response.json()["detail"]
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_auth_failure_flow_missing_credentials(self) -> None:
        """Test 401 response for missing authentication."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = True
                mock_settings.jwt_enabled = False
                mock_settings.api_keys = {TEST_API_KEY}

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    # No auth headers
                    response = await client.get("/forecast/London")

                assert response.status_code == 401
                assert response.json()["detail"] == "Missing authentication"
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_auth_failure_flow_invalid_api_key(self) -> None:
        """Test 403 response for invalid API key."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = True
                mock_settings.jwt_enabled = False
                mock_settings.api_keys = {TEST_API_KEY}

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get(
                        "/forecast/London",
                        headers={"X-API-Key": "invalid-key"},
                    )

                assert response.status_code == 403
                assert response.json()["detail"] == "Invalid API key"
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_complete_flow_multiple_cities(
        self,
        fake_redis: FakeAsyncRedis,
    ) -> None:
        """Test complete flow with multiple cities."""
        # Set up responses for multiple cities
        respx.get(GEOCODING_URL).mock(
            side_effect=[
                mock_geocoding_response("London", 51.5074, -0.1278),
                mock_geocoding_response("Paris", 48.8566, 2.3522),
                mock_geocoding_response("Tokyo", 35.6762, 139.6503),
            ]
        )
        respx.get(WEATHER_URL).mock(
            side_effect=[
                mock_weather_response(temperature=15.5, weather_code=2),
                mock_weather_response(temperature=18.0, weather_code=1),
                mock_weather_response(temperature=22.0, weather_code=0),
            ]
        )

        original_client = cache_module._redis_client
        cache_module._redis_client = fake_redis  # type: ignore[assignment]

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = False
                mock_settings.jwt_enabled = False

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    # Request weather for multiple cities
                    london = await client.get("/forecast/London")
                    paris = await client.get("/forecast/Paris")
                    tokyo = await client.get("/forecast/Tokyo")

                # All should succeed
                assert london.status_code == 200
                assert paris.status_code == 200
                assert tokyo.status_code == 200

                # Verify different temperatures
                assert london.json()["temperature"] == 15.5
                assert paris.json()["temperature"] == 18.0
                assert tokyo.json()["temperature"] == 22.0
        finally:
            cache_module._redis_client = original_client

    @respx.mock
    async def test_request_id_header_returned(self) -> None:
        """Test that X-Request-ID header is returned in responses."""
        respx.get(GEOCODING_URL).mock(return_value=mock_geocoding_response())
        respx.get(WEATHER_URL).mock(return_value=mock_weather_response())

        original_client = cache_module._redis_client
        cache_module._redis_client = None

        try:
            with patch("weather_api.auth.settings") as mock_settings:
                mock_settings.api_key_enabled = False
                mock_settings.jwt_enabled = False

                async with AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                ) as client:
                    response = await client.get("/forecast/London")

                assert response.status_code == 200
                assert "X-Request-ID" in response.headers
                # Request ID should be a valid UUID format
                request_id = response.headers["X-Request-ID"]
                assert len(request_id) == 36  # UUID format: 8-4-4-4-12
        finally:
            cache_module._redis_client = original_client
