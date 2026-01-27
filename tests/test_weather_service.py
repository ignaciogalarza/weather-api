"""Unit tests for the weather service."""

import pytest
import respx
from httpx import Response

from weather_api.schemas import Coordinates
from weather_api.services.weather import (
    GEOCODING_URL,
    WEATHER_URL,
    CityNotFoundError,
    WeatherServiceError,
    get_conditions,
    get_coordinates,
    get_current_weather,
)


class TestGetCoordinates:
    """Tests for get_coordinates function."""

    @respx.mock
    async def test_returns_coordinates_for_valid_city(self) -> None:
        """Should return coordinates when city is found."""
        respx.get(GEOCODING_URL).mock(
            return_value=Response(
                200,
                json={
                    "results": [
                        {"latitude": 40.7128, "longitude": -74.0060}
                    ]
                },
            )
        )

        coords = await get_coordinates("New York")

        assert coords.latitude == 40.7128
        assert coords.longitude == -74.0060

    @respx.mock
    async def test_raises_city_not_found_for_empty_results(self) -> None:
        """Should raise CityNotFoundError when results array is empty."""
        respx.get(GEOCODING_URL).mock(
            return_value=Response(200, json={"results": []})
        )

        with pytest.raises(CityNotFoundError, match="City not found"):
            await get_coordinates("NonexistentCity")

    @respx.mock
    async def test_raises_city_not_found_for_missing_results_key(self) -> None:
        """Should raise CityNotFoundError when results key is missing."""
        respx.get(GEOCODING_URL).mock(
            return_value=Response(200, json={})
        )

        with pytest.raises(CityNotFoundError, match="City not found"):
            await get_coordinates("InvalidCity")

    @respx.mock
    async def test_raises_service_error_on_api_failure(self) -> None:
        """Should raise WeatherServiceError on non-200 response."""
        respx.get(GEOCODING_URL).mock(return_value=Response(500))

        with pytest.raises(WeatherServiceError, match="Geocoding API error: 500"):
            await get_coordinates("London")

    @respx.mock
    async def test_raises_service_error_on_rate_limit(self) -> None:
        """Should raise WeatherServiceError on rate limit (429)."""
        respx.get(GEOCODING_URL).mock(return_value=Response(429))

        with pytest.raises(WeatherServiceError, match="Geocoding API error: 429"):
            await get_coordinates("Paris")


class TestGetCurrentWeather:
    """Tests for get_current_weather function."""

    @respx.mock
    async def test_returns_weather_data(self) -> None:
        """Should return weather data for valid coordinates."""
        respx.get(WEATHER_URL).mock(
            return_value=Response(
                200,
                json={
                    "current": {
                        "temperature_2m": 22.5,
                        "relative_humidity_2m": 65,
                        "wind_speed_10m": 8.2,
                        "weather_code": 0,
                    }
                },
            )
        )

        coords = Coordinates(latitude=51.5074, longitude=-0.1278)
        weather = await get_current_weather(coords)

        assert weather["temperature"] == 22.5
        assert weather["humidity"] == 65
        assert weather["wind_speed"] == 8.2
        assert weather["weather_code"] == 0

    @respx.mock
    async def test_raises_service_error_on_api_failure(self) -> None:
        """Should raise WeatherServiceError on non-200 response."""
        respx.get(WEATHER_URL).mock(return_value=Response(503))

        coords = Coordinates(latitude=51.5074, longitude=-0.1278)

        with pytest.raises(WeatherServiceError, match="Weather API error: 503"):
            await get_current_weather(coords)


class TestGetConditions:
    """Tests for get_conditions function."""

    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            (0, "Clear sky"),
            (1, "Mainly clear"),
            (2, "Partly cloudy"),
            (3, "Overcast"),
            (45, "Foggy"),
            (61, "Slight rain"),
            (65, "Heavy rain"),
            (71, "Slight snow"),
            (75, "Heavy snow"),
            (95, "Thunderstorm"),
        ],
    )
    def test_maps_known_weather_codes(self, code: int, expected: str) -> None:
        """Should return correct condition string for known codes."""
        assert get_conditions(code) == expected

    def test_returns_unknown_for_unmapped_code(self) -> None:
        """Should return 'Unknown' for unmapped weather codes."""
        assert get_conditions(999) == "Unknown"
        assert get_conditions(-1) == "Unknown"
