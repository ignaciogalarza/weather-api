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

## Skill: Architecture Diagrams (C4 + Sequence)

You are able to generate architecture diagrams for this project using the C4 model and sequence diagrams.

### C4 Model Rules
- Level 1: System Context Diagram
  - Show the Weather API as the central system.
  - Show external systems such as OpenWeatherMap, users, and Kubernetes cluster.
- Level 2: Container Diagram
  - Show FastAPI app, Redis (future), Postgres (future), external APIs, Docker container, Kubernetes pods.
- Level 3: Component Diagram
  - Show internal modules: routes, services, schemas, clients, config.
- Level 4: Code Diagram (optional)
  - Show class-level or function-level relationships when requested.

### Diagram Format
- Use Mermaid by default.
- Use PlantUML if explicitly requested.
- Always include a short explanation of the diagram.

### Sequence Diagrams
When asked for a sequence diagram, follow this structure:
- Actor (User or Client)
- FastAPI Router
- Service Layer
- External API (OpenWeatherMap)
- Response flow back to the user

### Requirements
- Diagrams must reflect the actual project structure.
- Use clean naming: WeatherAPI, ForecastService, OpenWeatherClient, etc.
- Keep diagrams simple unless asked for more detail.
- Always validate assumptions with the user if something is unclear.

### Examples of commands this skill should support:
- "Create a C4 Level 1 diagram for the Weather API."
- "Show a C4 container diagram including Docker and Kubernetes."
- "Generate a sequence diagram for GET /forecast/{city}."
- "Update the architecture diagram after adding Redis caching."

