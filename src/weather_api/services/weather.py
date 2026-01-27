"""Weather service for fetching data from Open-Meteo API."""

import httpx

from weather_api.schemas import Coordinates

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes
# https://open-meteo.com/en/docs
WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class CityNotFoundError(Exception):
    """Raised when a city cannot be found."""


class WeatherServiceError(Exception):
    """Raised when the weather service fails."""


async def get_coordinates(city: str) -> Coordinates:
    """Get coordinates for a city using Open-Meteo Geocoding API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GEOCODING_URL,
            params={"name": city, "count": 1},
        )

        if response.status_code != 200:
            raise WeatherServiceError(f"Geocoding API error: {response.status_code}")

        data = response.json()

        if "results" not in data or len(data["results"]) == 0:
            raise CityNotFoundError(f"City not found: {city}")

        result = data["results"][0]
        return Coordinates(
            latitude=result["latitude"],
            longitude=result["longitude"],
        )


async def get_current_weather(
    coords: Coordinates,
) -> dict[str, float | int]:
    """Get current weather for coordinates using Open-Meteo Weather API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            WEATHER_URL,
            params={
                "latitude": coords.latitude,
                "longitude": coords.longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                ),
            },
        )

        if response.status_code != 200:
            raise WeatherServiceError(f"Weather API error: {response.status_code}")

        data = response.json()
        current = data["current"]

        return {
            "temperature": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
        }


def get_conditions(weather_code: int) -> str:
    """Convert WMO weather code to human-readable conditions."""
    return WMO_CODES.get(weather_code, "Unknown")
