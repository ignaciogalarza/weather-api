"""Weather service for fetching data from Open-Meteo API."""

import time

import httpx
import structlog
from opentelemetry import trace

from weather_api.observability.metrics import (
    EXTERNAL_API_LATENCY,
    EXTERNAL_API_REQUESTS,
)
from weather_api.schemas import Coordinates

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

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
    with tracer.start_as_current_span("geocoding") as span:
        span.set_attribute("city", city)
        span.set_attribute("api", "open-meteo-geocoding")

        logger.info("geocoding_started", city=city)
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    GEOCODING_URL,
                    params={"name": city, "count": 1},
                )

            duration = time.perf_counter() - start_time
            EXTERNAL_API_LATENCY.labels(api="geocoding").observe(duration)
            span.set_attribute("status_code", response.status_code)

            if response.status_code != 200:
                EXTERNAL_API_REQUESTS.labels(api="geocoding", status="error").inc()
                logger.error(
                    "geocoding_failed",
                    city=city,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                )
                raise WeatherServiceError(
                    f"Geocoding API error: {response.status_code}"
                )

            data = response.json()

            if "results" not in data or len(data["results"]) == 0:
                EXTERNAL_API_REQUESTS.labels(api="geocoding", status="not_found").inc()
                logger.warning("city_not_found", city=city)
                raise CityNotFoundError(f"City not found: {city}")

            result = data["results"][0]
            coords = Coordinates(
                latitude=result["latitude"],
                longitude=result["longitude"],
            )

            EXTERNAL_API_REQUESTS.labels(api="geocoding", status="success").inc()
            span.set_attribute("latitude", coords.latitude)
            span.set_attribute("longitude", coords.longitude)
            logger.info(
                "geocoding_completed",
                city=city,
                latitude=coords.latitude,
                longitude=coords.longitude,
                duration_ms=round(duration * 1000, 2),
            )

            return coords

        except (httpx.RequestError, httpx.TimeoutException) as e:
            duration = time.perf_counter() - start_time
            EXTERNAL_API_LATENCY.labels(api="geocoding").observe(duration)
            EXTERNAL_API_REQUESTS.labels(api="geocoding", status="error").inc()
            logger.error("geocoding_request_failed", city=city, error=str(e))
            raise WeatherServiceError(f"Geocoding request failed: {e}") from e


async def get_current_weather(
    coords: Coordinates,
) -> dict[str, float | int]:
    """Get current weather for coordinates using Open-Meteo Weather API."""
    with tracer.start_as_current_span("weather_fetch") as span:
        span.set_attribute("latitude", coords.latitude)
        span.set_attribute("longitude", coords.longitude)
        span.set_attribute("api", "open-meteo-weather")

        logger.info(
            "weather_fetch_started",
            latitude=coords.latitude,
            longitude=coords.longitude,
        )
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    WEATHER_URL,
                    params={
                        "latitude": coords.latitude,
                        "longitude": coords.longitude,
                        "current": (
                            "temperature_2m,relative_humidity_2m,"
                            "wind_speed_10m,weather_code"
                        ),
                    },
                )

            duration = time.perf_counter() - start_time
            EXTERNAL_API_LATENCY.labels(api="weather").observe(duration)
            span.set_attribute("status_code", response.status_code)

            if response.status_code != 200:
                EXTERNAL_API_REQUESTS.labels(api="weather", status="error").inc()
                logger.error(
                    "weather_fetch_failed",
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                )
                raise WeatherServiceError(f"Weather API error: {response.status_code}")

            data = response.json()
            current = data["current"]

            weather_data = {
                "temperature": current["temperature_2m"],
                "humidity": current["relative_humidity_2m"],
                "wind_speed": current["wind_speed_10m"],
                "weather_code": current["weather_code"],
            }

            EXTERNAL_API_REQUESTS.labels(api="weather", status="success").inc()
            span.set_attribute("temperature", weather_data["temperature"])
            span.set_attribute("weather_code", weather_data["weather_code"])
            logger.info(
                "weather_fetch_completed",
                temperature=weather_data["temperature"],
                weather_code=weather_data["weather_code"],
                duration_ms=round(duration * 1000, 2),
            )

            return weather_data

        except (httpx.RequestError, httpx.TimeoutException) as e:
            duration = time.perf_counter() - start_time
            EXTERNAL_API_LATENCY.labels(api="weather").observe(duration)
            EXTERNAL_API_REQUESTS.labels(api="weather", status="error").inc()
            logger.error("weather_request_failed", error=str(e))
            raise WeatherServiceError(f"Weather request failed: {e}") from e


def get_conditions(weather_code: int) -> str:
    """Convert WMO weather code to human-readable conditions."""
    return WMO_CODES.get(weather_code, "Unknown")
