# ADR 0001: Use Open-Meteo API for Weather Data

## Status

Accepted

## Date

2026-01-27

## Context

We need a weather data provider for the Weather API. The options considered were:

1. **OpenWeatherMap** - Popular, requires API key registration
2. **Open-Meteo** - Free, no API key required
3. **WeatherAPI** - Freemium, requires API key

## Decision

We will use **Open-Meteo** for both geocoding and weather data.

## Rationale

- **No API key required**: Simplifies development and deployment
- **Free tier**: No cost for reasonable usage
- **Two APIs in one**: Provides both geocoding and weather data
- **Good documentation**: Clear API reference
- **Reliable**: Open-source backed project

## Consequences

### Positive

- Zero configuration for API keys
- No secrets management needed
- Easy local development
- No vendor lock-in concerns

### Negative

- Less feature-rich than paid alternatives
- No historical data in free tier
- Rate limits may apply for high traffic

## API Endpoints Used

- Geocoding: `https://geocoding-api.open-meteo.com/v1/search`
- Weather: `https://api.open-meteo.com/v1/forecast`

## References

- [Open-Meteo Documentation](https://open-meteo.com/en/docs)
- [Open-Meteo GitHub](https://github.com/open-meteo/open-meteo)
