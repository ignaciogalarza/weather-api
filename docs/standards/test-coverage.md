# Test Coverage Standards

## Requirements

- **Minimum Coverage: 90%**
- Coverage below 90% blocks merge
- New features require tests before PR

## Running Coverage

```bash
# Run tests with coverage report
uv run pytest --cov=weather_api --cov-report=term-missing

# Generate HTML report
uv run pytest --cov=weather_api --cov-report=html
open htmlcov/index.html

# Fail if below threshold
uv run pytest --cov=weather_api --cov-fail-under=90
```

## Coverage Configuration

Add to `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src/weather_api"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
fail_under = 90
```

## What to Test

### Unit Tests
- Individual functions in isolation
- All code paths (success, error, edge cases)
- Mock external dependencies

### Integration Tests
- Endpoint request/response cycles
- Error responses (4xx, 5xx)
- Input validation

### Required Coverage

| Component | Minimum | Target |
|-----------|---------|--------|
| Routes | 90% | 100% |
| Services | 90% | 100% |
| Schemas | 90% | 95% |
| Overall | 90% | 95% |

## Test Structure

```python
"""Tests for the weather service."""

import pytest
from weather_api.services.weather import get_coordinates


class TestGetCoordinates:
    """Tests for get_coordinates function."""

    async def test_returns_coordinates_for_valid_city(self) -> None:
        """Should return coordinates when city is found."""
        # Arrange
        # Act
        # Assert

    async def test_raises_error_for_invalid_city(self) -> None:
        """Should raise CityNotFoundError for unknown city."""
        with pytest.raises(CityNotFoundError):
            await get_coordinates("InvalidCity")
```

## Current Coverage

```
tests/test_main.py              1 test
tests/test_forecast.py          5 tests
tests/test_weather_service.py   18 tests
─────────────────────────────────────────
Total                           24 tests
```

## CI Integration

Coverage check should be part of CI pipeline:

```yaml
- name: Run tests with coverage
  run: uv run pytest --cov=weather_api --cov-fail-under=90
```
