# Commit Message Guidelines

## Format

Every commit message must follow this structure:

```
<type>: <short description (imperative, max 50 chars)>

<end-user paragraph - what this means for users>

<technical paragraph - implementation details for developers>

Co-Authored-By: <name> <email>
```

## Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | feat: add weather forecast endpoint |
| `fix` | Bug fix | fix: handle empty city names |
| `docs` | Documentation | docs: add API reference |
| `test` | Test additions | test: add coverage for error cases |
| `refactor` | Code restructuring | refactor: extract weather client |
| `perf` | Performance | perf: cache geocoding results |
| `chore` | Maintenance | chore: update dependencies |

## Paragraph Guidelines

### End-User Paragraph
Write as if explaining to a non-technical stakeholder:
- What can users do now?
- What problem does this solve?
- What changed from their perspective?

**Good**: "Users can now get weather forecasts for any city worldwide by name."
**Bad**: "Added GET endpoint with Pydantic model validation."

### Technical Paragraph
Write for developers who will maintain this code:
- What was implemented?
- What patterns/libraries used?
- What files were changed?
- Test coverage notes

**Good**: "Integrates Open-Meteo API with async httpx client. Adds service layer with geocoding and weather fetching. Full test coverage using respx mocks."
**Bad**: "Added some files and tests."

## Examples from This Project

### Feature Commit
```
feat: add weather forecast endpoint for any city

Users can now get current weather information for any city by calling
GET /forecast/{city}. The response includes temperature (Celsius),
humidity (%), wind speed (km/h), and weather conditions in plain English
(e.g., "Partly cloudy", "Light rain"). Returns a clear error message
if the city is not found.

Integrates with Open-Meteo API (free, no key required) for weather data.
Adds modular architecture: schemas.py for Pydantic models, services/weather.py
for API client with geocoding, routes/forecast.py for endpoint handler.
Includes httpx for async HTTP calls and respx for mocking in tests.
Full test coverage for success, 404, and 503 error cases.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Test Commit
```
test: add comprehensive test coverage for weather service

Ensures the weather forecast feature works reliably across different
scenarios: valid cities, unknown cities, cities with spaces in names,
and when external weather services are temporarily unavailable.

Adds unit tests for weather service layer (get_coordinates, get_current_weather,
get_conditions) covering success paths, error handling, and edge cases.
Expands integration tests for /forecast endpoint to cover weather API failures
after successful geocoding and URL-encoded city names. Uses pytest parametrize
for WMO weather code mappings. Total: 24 tests.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Documentation Commit
```
docs: add professional documentation structure with C4 and sequence diagrams

Creates comprehensive documentation for the Weather API including:
architecture diagrams showing system context and request flows,
API reference with all endpoints and response formats, getting
started guide for new developers, and deployment instructions
for Docker and Kubernetes.

Adds docs/ folder structure following industry standards:
- architecture/ - C4 Level 1 context diagram, sequence diagrams
- api/ - Endpoint reference with request/response examples
- guides/ - Getting started and deployment guides
- adr/ - Architecture Decision Records

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

## Validation

Before committing, ensure:
1. Message follows the format
2. Type is appropriate
3. Both paragraphs are present
4. Co-author line is included
5. Description is clear and accurate
