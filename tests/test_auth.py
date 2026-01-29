"""Tests for API key authentication."""

from unittest.mock import patch

import respx
from httpx import ASGITransport, AsyncClient, Response

from weather_api.main import app
from weather_api.services.weather import GEOCODING_URL, WEATHER_URL


def _mock_weather_apis() -> None:
    """Set up mocks for geocoding and weather APIs."""
    respx.get(GEOCODING_URL).mock(
        return_value=Response(
            200,
            json={
                "results": [
                    {
                        "name": "London",
                        "latitude": 51.5074,
                        "longitude": -0.1278,
                    }
                ]
            },
        )
    )
    respx.get(WEATHER_URL).mock(
        return_value=Response(
            200,
            json={
                "current": {
                    "temperature_2m": 15.5,
                    "relative_humidity_2m": 72,
                    "wind_speed_10m": 12.3,
                    "weather_code": 2,
                }
            },
        )
    )


@respx.mock
async def test_auth_disabled_allows_request_without_key() -> None:
    """When all auth is disabled, requests work without credentials."""
    _mock_weather_apis()

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.api_key_enabled = False
        mock_settings.jwt_enabled = False

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/forecast/London")

    assert response.status_code == 200


@respx.mock
async def test_api_key_enabled_missing_key_returns_401() -> None:
    """When API key auth is enabled, missing key returns 401."""
    _mock_weather_apis()

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.jwt_enabled = False
        mock_settings.api_keys = {"valid-key"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/forecast/London")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authentication"


@respx.mock
async def test_api_key_enabled_invalid_key_returns_403() -> None:
    """When API key auth is enabled, invalid key returns 403."""
    _mock_weather_apis()

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.jwt_enabled = False
        mock_settings.api_keys = {"valid-key"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/forecast/London", headers={"X-API-Key": "invalid-key"}
            )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid API key"


@respx.mock
async def test_api_key_enabled_valid_key_returns_200() -> None:
    """When API key auth is enabled, valid key returns 200."""
    _mock_weather_apis()

    with patch("weather_api.auth.settings") as mock_settings:
        mock_settings.api_key_enabled = True
        mock_settings.jwt_enabled = False
        mock_settings.api_keys = {"valid-key"}

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/forecast/London", headers={"X-API-Key": "valid-key"}
            )

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"
