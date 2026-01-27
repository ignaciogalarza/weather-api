# Skill: Observability

## Purpose

Implement comprehensive observability (logging, metrics, tracing) to monitor and debug the Weather API in production.

## Triggers

- "Add observability"
- "Implement logging"
- "Add metrics"
- "Set up tracing"
- "Monitor the API"
- "Add Prometheus metrics"

## Rules

### Three Pillars of Observability

| Pillar | Tool | Purpose |
|--------|------|---------|
| Logs | Structlog | Debug information, audit trail |
| Metrics | Prometheus | Performance monitoring, alerting |
| Traces | OpenTelemetry | Request flow, latency analysis |

### Logging Standards

| Level | Use Case |
|-------|----------|
| DEBUG | Development debugging |
| INFO | Normal operations, request/response |
| WARNING | Recoverable issues |
| ERROR | Failures requiring attention |
| CRITICAL | System-wide failures |

### Required Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | Counter | method, endpoint, status |
| `http_request_duration_seconds` | Histogram | method, endpoint |
| `external_api_requests_total` | Counter | api, status |
| `external_api_duration_seconds` | Histogram | api |

### Trace Context

All traces must include:
- Service name
- Request ID
- User context (if available)
- External API calls as child spans

## Examples

### Adding Structured Logging

```python
import structlog

logger = structlog.get_logger()

@router.get("/forecast/{city}")
async def get_forecast(city: str) -> ForecastResponse:
    logger.info("forecast_requested", city=city)
    try:
        result = await get_weather(city)
        logger.info("forecast_success", city=city, temperature=result.temperature)
        return result
    except CityNotFoundError:
        logger.warning("city_not_found", city=city)
        raise
```

### Adding Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

### Adding OpenTelemetry Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def get_coordinates(city: str) -> Coordinates:
    with tracer.start_as_current_span("geocoding") as span:
        span.set_attribute("city", city)
        response = await client.get(GEOCODING_URL, params={"name": city})
        span.set_attribute("status_code", response.status_code)
        return parse_coordinates(response)
```

## Extensions

### Grafana Dashboards

Create dashboards for:
- Request rate and latency
- Error rate by endpoint
- External API health
- Resource utilization

### Alerting Rules

```yaml
groups:
  - name: weather-api
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
```

See [Observability Plan](../plans/observability.md) for full implementation details.
