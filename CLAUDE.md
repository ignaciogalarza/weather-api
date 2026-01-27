# Weather API

Weather forecast API that returns current weather conditions for any city worldwide.

## Tech Stack

- **Python 3.12** - Runtime
- **FastAPI** - Web framework
- **UV** - Package management
- **MyPy** - Static type checking (strict mode)
- **Ruff** - Linting and formatting
- **Pytest** - Testing with async support
- **Docker** - Containerization
- **Kubernetes** - Orchestration (k3d for local)

## Project Structure

```
src/weather_api/
├── __init__.py           # Package version
├── main.py               # FastAPI app, router mounting
├── schemas.py            # Pydantic models (Coordinates, ForecastResponse)
├── routes/
│   └── forecast.py       # GET /forecast/{city} endpoint
└── services/
    └── weather.py        # Open-Meteo API client, geocoding

tests/
├── test_main.py          # Health check tests
├── test_forecast.py      # Endpoint integration tests
└── test_weather_service.py  # Service unit tests

k8s/
├── deployments/
│   └── weather-api.yaml  # 2 replicas, health probes
└── services/
    └── weather-api.yaml  # NodePort 30080
```

## Code Standards

- All functions must have type annotations (MyPy strict)
- Line length: 88 characters
- Use `raise ... from` for exception chaining
- Async functions for I/O operations
- Pydantic models for request/response schemas
- Tests required for all new features

## Common Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn weather_api.main:app --reload

# Run linter
uv run ruff check src tests

# Run type checker
uv run mypy

# Run tests
uv run pytest -v

# Run all checks
uv run ruff check src tests && uv run mypy && uv run pytest

# Build Docker image
docker build -t weather-api:latest .

# Deploy to Kubernetes
kubectl apply -f k8s/deployments/weather-api.yaml
kubectl apply -f k8s/services/weather-api.yaml

# Access via port-forward
kubectl port-forward svc/weather-api 8080:80
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/forecast/{city}` | Current weather for city |

## External Dependencies

- **Open-Meteo Geocoding API** - City name to coordinates
- **Open-Meteo Weather API** - Current weather data (free, no API key)
