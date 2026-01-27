"""Forecast route handlers."""

from fastapi import APIRouter, HTTPException

from weather_api.schemas import ForecastResponse
from weather_api.services.weather import (
    CityNotFoundError,
    WeatherServiceError,
    get_conditions,
    get_coordinates,
    get_current_weather,
)

router = APIRouter(tags=["forecast"])


@router.get(
    "/forecast/{city}",
    response_model=ForecastResponse,
    summary="Get weather forecast for a city",
    description="Returns current weather conditions including temperature, humidity, "
    "wind speed, and weather conditions for the specified city.",
    responses={
        200: {"description": "Weather data retrieved successfully"},
        404: {"description": "City not found"},
        503: {"description": "Weather service unavailable"},
    },
)
async def get_forecast(city: str) -> ForecastResponse:
    """Get current weather forecast for a city."""
    try:
        coords = await get_coordinates(city)
        weather = await get_current_weather(coords)

        return ForecastResponse(
            city=city,
            temperature=weather["temperature"],
            humidity=int(weather["humidity"]),
            wind_speed=weather["wind_speed"],
            conditions=get_conditions(int(weather["weather_code"])),
        )
    except CityNotFoundError:
        raise HTTPException(status_code=404, detail=f"City not found: {city}") from None
    except WeatherServiceError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
