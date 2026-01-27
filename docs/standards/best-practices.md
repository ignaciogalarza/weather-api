# Best Practices

This document establishes the standards and best practices for the Weather API project. All contributors must follow these guidelines.

## Code Quality

### Type Safety
- **MyPy strict mode** is mandatory
- All functions must have complete type annotations
- No `Any` types unless absolutely necessary with justification
- Use Pydantic models for data validation

### Linting
- **Ruff** for all linting and formatting
- Zero tolerance for linting errors
- Line length: 88 characters maximum
- Import sorting via isort rules

### Code Style
- Use `raise ... from` for exception chaining
- Async functions for all I/O operations
- Single responsibility principle for functions
- Meaningful variable and function names

## Testing

### Coverage Requirements
- **Minimum 90% test coverage** - non-negotiable
- All new features require tests before merge
- Both unit tests and integration tests required
- Edge cases and error scenarios must be tested

### Test Structure
```
tests/
├── test_<module>.py      # Unit tests per module
├── test_<endpoint>.py    # Integration tests per endpoint
└── conftest.py           # Shared fixtures
```

### Test Naming
```python
def test_<function>_<scenario>_<expected_result>() -> None:
    """Test description."""
```

## Documentation

### Required Documentation
1. **C4 Diagrams** - All architectural changes require diagram updates
   - Level 1: System Context (mandatory)
   - Level 2: Container (for infrastructure changes)
   - Level 3: Component (for major feature additions)

2. **ADR (Architecture Decision Records)** - Required for:
   - New external dependencies
   - Technology choices
   - Significant architectural changes
   - Breaking changes

3. **API Documentation** - All endpoints documented with:
   - Request/response examples
   - Error scenarios
   - Parameter descriptions

### Diagram Format
- Use Mermaid syntax
- Keep diagrams in `docs/architecture/`
- Update diagrams when architecture changes

## Version Control

### Commit Messages
Follow the format established in this project:

```
<type>: <short description>

<end-user explanation paragraph>

<technical details paragraph>

Co-Authored-By: <author>
```

**Types**: feat, fix, docs, test, refactor, chore, perf

### Example
```
feat: add weather forecast endpoint for any city

Users can now get current weather information for any city by calling
GET /forecast/{city}. The response includes temperature, humidity,
wind speed, and conditions in plain English.

Integrates with Open-Meteo API for weather data. Adds modular
architecture with schemas.py, services/weather.py, routes/forecast.py.
Full test coverage for success and error scenarios.

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Branch Strategy
- `master` - production-ready code
- `feature/*` - new features
- `fix/*` - bug fixes
- `docs/*` - documentation updates

## Deployment

### Container Requirements
- **Docker** is mandatory for all deployments
- Multi-stage builds for minimal image size
- No root user in containers
- Health checks configured

### Kubernetes Requirements
- All services deployed via **Kubernetes manifests**
- Resource limits defined (CPU, memory)
- Liveness and readiness probes configured
- Horizontal Pod Autoscaler for scaling

### Manifest Structure
```
k8s/
├── deployments/    # Deployment manifests
├── services/       # Service manifests
├── configmaps/     # Configuration
├── secrets/        # Secret references
└── ingress/        # Ingress rules
```

## Peer Review

### Review Checklist
Before approving any PR, verify:

- [ ] Tests pass with >= 90% coverage
- [ ] MyPy strict passes
- [ ] Ruff check passes
- [ ] Documentation updated (if applicable)
- [ ] C4 diagrams updated (if architecture changed)
- [ ] ADR created (if decision made)
- [ ] Commit messages follow standard
- [ ] No security vulnerabilities introduced

### Review Process
1. Author creates PR with description
2. Automated checks run (tests, lint, types)
3. Reviewer verifies checklist
4. Reviewer tests locally if needed
5. Approval and merge

## Security

- No secrets in code or commits
- Use environment variables for configuration
- Validate all external input
- Keep dependencies updated
- Regular security audits
