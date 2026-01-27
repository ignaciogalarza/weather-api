# Skill: Performance

## Purpose

Benchmark, analyze, and optimize the Weather API performance to meet latency and throughput requirements.

## Triggers

- "Run performance tests"
- "Benchmark the API"
- "Optimize performance"
- "Load test the endpoint"
- "Check latency"
- "Performance analysis"

## Rules

### Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| P50 Latency | < 200ms | < 300ms |
| P95 Latency | < 500ms | < 1000ms |
| P99 Latency | < 1000ms | < 2000ms |
| Throughput | > 100 RPS | > 50 RPS |
| Error Rate | < 0.1% | < 1% |

### Benchmarking Tools

| Tool | Use Case |
|------|----------|
| Locust | Load testing, user scenarios |
| wrk | Raw HTTP benchmarking |
| pytest-benchmark | Function-level benchmarks |
| py-spy | CPU profiling |
| memray | Memory profiling |

### Optimization Priorities

1. **External API calls** - Cache, connection pooling
2. **Serialization** - Pydantic v2, orjson
3. **Async efficiency** - Connection reuse
4. **Memory** - Response streaming for large payloads

## Examples

### Quick Benchmark with wrk

```bash
# Start the server
uv run uvicorn weather_api.main:app --workers 4

# Run benchmark
wrk -t4 -c100 -d30s http://localhost:8000/health
wrk -t4 -c100 -d30s http://localhost:8000/forecast/London
```

### Load Test with Locust

```python
# locustfile.py
from locust import HttpUser, task, between

class WeatherAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(10)
    def get_forecast(self):
        cities = ["London", "Paris", "Tokyo", "New York"]
        city = random.choice(cities)
        self.client.get(f"/forecast/{city}")
```

```bash
# Run Locust
locust -f locustfile.py --host=http://localhost:8000
```

### Function Benchmark with pytest

```python
# tests/test_performance.py
import pytest

@pytest.mark.benchmark
def test_get_conditions_performance(benchmark):
    """Benchmark weather code mapping."""
    from weather_api.services.weather import get_conditions

    result = benchmark(get_conditions, 2)
    assert result == "Partly cloudy"
```

## Optimization Techniques

### Connection Pooling

```python
# Reuse HTTP client
client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    timeout=httpx.Timeout(10.0, connect=5.0)
)
```

### Response Caching

```python
from cachetools import TTLCache

cache = TTLCache(maxsize=1000, ttl=300)  # 5 min TTL

async def get_coordinates_cached(city: str) -> Coordinates:
    if city in cache:
        return cache[city]
    coords = await get_coordinates(city)
    cache[city] = coords
    return coords
```

### Faster JSON

```python
# Use orjson for faster serialization
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)
```

## Commands

```bash
# CPU profiling
py-spy record -o profile.svg -- python -m uvicorn weather_api.main:app

# Memory profiling
memray run -o output.bin python -m uvicorn weather_api.main:app
memray flamegraph output.bin

# Async profiling
python -m asyncio_profiler ...
```

See [Performance Plan](../plans/performance-benchmark.md) for full benchmarking strategy.
