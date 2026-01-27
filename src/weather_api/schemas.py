"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel


class Coordinates(BaseModel):
    """Geographic coordinates."""

    latitude: float
    longitude: float


class ForecastResponse(BaseModel):
    """Weather forecast response."""

    city: str
    temperature: float  # Celsius
    humidity: int  # Percentage
    wind_speed: float  # km/h
    conditions: str  # e.g., "Clear", "Cloudy", "Rain"
