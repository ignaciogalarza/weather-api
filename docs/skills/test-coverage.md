# Skill: Test Coverage

## Purpose

Ensure all code changes maintain or exceed 90% test coverage with comprehensive test scenarios.

## Triggers

- "Check test coverage"
- "Add tests for..."
- "What's the coverage?"
- "Tests needed for this feature"
- "Coverage report"

## Rules

### Coverage Requirements

| Metric | Minimum | Target |
|--------|---------|--------|
| Line Coverage | 90% | 95% |
| Branch Coverage | 85% | 90% |
| New Code Coverage | 95% | 100% |

### Test Categories

#### Unit Tests
- Test individual functions in isolation
- Mock all external dependencies
- Cover all code paths
- Location: `tests/test_<module>.py`

#### Integration Tests
- Test endpoint request/response
- Test service interactions
- Use test fixtures
- Location: `tests/test_<feature>.py`

#### Edge Case Tests
- Empty inputs
- Invalid inputs
- Boundary conditions
- Unicode/special characters

### Test Structure

```python
class Test<Component>:
    """Tests for <component>."""

    async def test_<action>_<scenario>_<result>(self) -> None:
        """Should <expected behavior>."""
        # Arrange
        input_data = ...

        # Act
        result = await function(input_data)

        # Assert
        assert result == expected
```

### Mocking Guidelines

| External Dependency | Mock Tool |
|--------------------|-----------|
| HTTP APIs | respx |
| Databases | pytest fixtures |
| Time | freezegun |
| Environment | monkeypatch |

## Examples

### Adding Tests for New Feature

**Input**: "Add tests for a new /forecast/extended endpoint"

**Output**:
```python
"""Tests for extended forecast endpoint."""

import respx
from httpx import Response

class TestExtendedForecast:
    """Tests for GET /forecast/extended/{city}."""

    @respx.mock
    async def test_returns_7_day_forecast(self) -> None:
        """Should return 7-day forecast for valid city."""
        # Mock external APIs
        respx.get(...).mock(return_value=Response(200, json={...}))

        # Make request
        response = await client.get("/forecast/extended/London")

        # Verify
        assert response.status_code == 200
        assert len(response.json()["daily"]) == 7

    @respx.mock
    async def test_returns_404_for_unknown_city(self) -> None:
        """Should return 404 for unknown city."""
        respx.get(...).mock(return_value=Response(200, json={}))

        response = await client.get("/forecast/extended/Unknown123")

        assert response.status_code == 404
```

### Coverage Report Interpretation

```
Name                                    Stmts   Miss Branch BrPart  Cover
-------------------------------------------------------------------------
src/weather_api/__init__.py                 2      0      0      0   100%
src/weather_api/main.py                    12      0      2      0   100%
src/weather_api/routes/forecast.py         18      0      4      0   100%
src/weather_api/schemas.py                 14      0      0      0   100%
src/weather_api/services/weather.py        45      2      8      1    94%
-------------------------------------------------------------------------
TOTAL                                      91      2     14      1    96%
```

## Commands

```bash
# Quick coverage check
uv run pytest --cov=weather_api

# Detailed report with missing lines
uv run pytest --cov=weather_api --cov-report=term-missing

# HTML report for detailed analysis
uv run pytest --cov=weather_api --cov-report=html

# Fail if under threshold
uv run pytest --cov=weather_api --cov-fail-under=90

# Coverage for specific file
uv run pytest --cov=weather_api.services.weather tests/test_weather_service.py
```

## Extensions

### Coverage Badges

Add to README:
```markdown
![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)
```

### CI Integration

```yaml
- name: Test with coverage
  run: |
    uv run pytest --cov=weather_api --cov-fail-under=90 --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```
