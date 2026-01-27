# Getting Started

## Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) package manager

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ignaciogalarza/weather-api.git
   cd weather-api
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Run the development server**
   ```bash
   uv run uvicorn weather_api.main:app --reload
   ```

4. **Test the API**
   ```bash
   # Health check
   curl http://localhost:8000/health

   # Get weather for a city
   curl http://localhost:8000/forecast/London
   ```

## Development Workflow

### Run Tests
```bash
uv run pytest -v
```

### Run Linter
```bash
uv run ruff check src tests
```

### Run Type Checker
```bash
uv run mypy
```

### Run All Checks
```bash
uv run ruff check src tests && uv run mypy && uv run pytest
```

## Project Structure

```
src/weather_api/
├── main.py           # Application entry point
├── schemas.py        # Pydantic models
├── routes/
│   └── forecast.py   # Endpoint handlers
└── services/
    └── weather.py    # External API client
```

## Next Steps

- [API Endpoints](../api/endpoints.md) - Full API reference
- [Deployment Guide](deployment.md) - Docker and Kubernetes deployment
- [Architecture](../architecture/c4-level1-context.md) - System design
