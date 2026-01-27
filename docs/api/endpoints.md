# API Endpoints

## Base URL

- **Local**: `http://localhost:8000`
- **Kubernetes**: `http://localhost:8080` (via port-forward)

## Endpoints

### Health Check

Check if the service is running.

```
GET /health
```

**Response** `200 OK`
```json
{
    "status": "healthy"
}
```

---

### Get Weather Forecast

Get current weather conditions for a city.

```
GET /forecast/{city}
```

**Parameters**

| Name | Type | Location | Description |
|------|------|----------|-------------|
| city | string | path | City name (e.g., "London", "New York", "Tokyo") |

**Response** `200 OK`
```json
{
    "city": "London",
    "temperature": 15.5,
    "humidity": 72,
    "wind_speed": 12.3,
    "conditions": "Partly cloudy"
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| city | string | Requested city name |
| temperature | float | Temperature in Celsius |
| humidity | integer | Relative humidity percentage |
| wind_speed | float | Wind speed in km/h |
| conditions | string | Human-readable weather conditions |

**Error Responses**

| Status | Description |
|--------|-------------|
| 404 | City not found |
| 503 | External weather service unavailable |

**Example Error** `404 Not Found`
```json
{
    "detail": "City not found: InvalidCity123"
}
```

## Weather Conditions

The `conditions` field maps to these values:

| Condition | Description |
|-----------|-------------|
| Clear sky | No clouds |
| Mainly clear | Few clouds |
| Partly cloudy | Scattered clouds |
| Overcast | Full cloud cover |
| Foggy | Fog or mist |
| Light drizzle | Light precipitation |
| Slight rain | Light rain |
| Moderate rain | Steady rain |
| Heavy rain | Intense rain |
| Slight snow | Light snowfall |
| Heavy snow | Intense snowfall |
| Thunderstorm | Thunder and lightning |
