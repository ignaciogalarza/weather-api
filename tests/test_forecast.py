"""Tests for the forecast endpoint."""

import respx
from httpx import ASGITransport, AsyncClient, Response

from weather_api.main import app
from weather_api.services.weather import GEOCODING_URL, WEATHER_URL


@respx.mock
async def test_get_forecast_success() -> None:
    """Test successful forecast retrieval."""
    # Mock geocoding response
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

    # Mock weather response
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

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/forecast/London")

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "London"
    assert data["temperature"] == 15.5
    assert data["humidity"] == 72
    assert data["wind_speed"] == 12.3
    assert data["conditions"] == "Partly cloudy"


@respx.mock
async def test_get_forecast_city_not_found() -> None:
    """Test 404 response for unknown city."""
    respx.get(GEOCODING_URL).mock(
        return_value=Response(200, json={})
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/forecast/UnknownCity123")

    assert response.status_code == 404
    assert "City not found" in response.json()["detail"]


@respx.mock
async def test_get_forecast_geocoding_error() -> None:
    """Test 503 response when geocoding API fails."""
    respx.get(GEOCODING_URL).mock(return_value=Response(500))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/forecast/London")

    assert response.status_code == 503


@respx.mock
async def test_get_forecast_weather_api_error() -> None:
    """Test 503 response when weather API fails after successful geocoding."""
    respx.get(GEOCODING_URL).mock(
        return_value=Response(
            200,
            json={"results": [{"latitude": 51.5074, "longitude": -0.1278}]},
        )
    )
    respx.get(WEATHER_URL).mock(return_value=Response(503))

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/forecast/London")

    assert response.status_code == 503


@respx.mock
async def test_get_forecast_with_spaces_in_city_name() -> None:
    """Test forecast for city with spaces in name."""
    respx.get(GEOCODING_URL).mock(
        return_value=Response(
            200,
            json={"results": [{"latitude": 40.7128, "longitude": -74.0060}]},
        )
    )
    respx.get(WEATHER_URL).mock(
        return_value=Response(
            200,
            json={
                "current": {
                    "temperature_2m": 18.0,
                    "relative_humidity_2m": 55,
                    "wind_speed_10m": 10.0,
                    "weather_code": 0,
                }
            },
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/forecast/New%20York")

    assert response.status_code == 200
    assert response.json()["city"] == "New York"
    assert response.json()["conditions"] == "Clear sky"
