# Sequence Diagram: GET /forecast/{city}

## Overview

This diagram shows the complete request flow when a client requests weather data for a city.

## Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant Router as FastAPI Router<br>/forecast/{city}
    participant Service as WeatherService
    participant GeoAPI as Open-Meteo<br>Geocoding API
    participant WeatherAPI as Open-Meteo<br>Weather API

    Client->>Router: GET /forecast/London
    Router->>Service: get_coordinates("London")
    Service->>GeoAPI: GET /v1/search?name=London&count=1
    GeoAPI-->>Service: {results: [{lat: 51.5, lon: -0.1}]}
    Service-->>Router: Coordinates(lat=51.5, lon=-0.1)

    Router->>Service: get_current_weather(coords)
    Service->>WeatherAPI: GET /v1/forecast?lat=51.5&lon=-0.1&current=...
    WeatherAPI-->>Service: {current: {temperature_2m: 15.5, ...}}
    Service-->>Router: {temperature: 15.5, humidity: 72, ...}

    Router->>Router: Build ForecastResponse
    Router-->>Client: 200 OK {city, temperature, humidity, wind_speed, conditions}
```

## Error Scenarios

### City Not Found (404)

```mermaid
sequenceDiagram
    participant Client
    participant Router as FastAPI Router
    participant Service as WeatherService
    participant GeoAPI as Open-Meteo<br>Geocoding API

    Client->>Router: GET /forecast/InvalidCity123
    Router->>Service: get_coordinates("InvalidCity123")
    Service->>GeoAPI: GET /v1/search?name=InvalidCity123
    GeoAPI-->>Service: {results: []}
    Service-->>Router: raises CityNotFoundError
    Router-->>Client: 404 Not Found {detail: "City not found: InvalidCity123"}
```

### External API Failure (503)

```mermaid
sequenceDiagram
    participant Client
    participant Router as FastAPI Router
    participant Service as WeatherService
    participant GeoAPI as Open-Meteo<br>Geocoding API

    Client->>Router: GET /forecast/London
    Router->>Service: get_coordinates("London")
    Service->>GeoAPI: GET /v1/search?name=London
    GeoAPI-->>Service: 500 Internal Server Error
    Service-->>Router: raises WeatherServiceError
    Router-->>Client: 503 Service Unavailable
```

## Response Structure

```json
{
    "city": "London",
    "temperature": 15.5,
    "humidity": 72,
    "wind_speed": 12.3,
    "conditions": "Partly cloudy"
}
```

## Code References

- Router: `src/weather_api/routes/forecast.py:17`
- Service: `src/weather_api/services/weather.py:45`
- Schema: `src/weather_api/schemas.py:13`
