"""Prometheus metrics configuration."""

from fastapi import FastAPI
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Custom metrics for external API calls
EXTERNAL_API_REQUESTS = Counter(
    "weather_api_external_requests_total",
    "Total external API requests",
    ["api", "status"],
)

EXTERNAL_API_LATENCY = Histogram(
    "weather_api_external_request_duration_seconds",
    "External API request latency in seconds",
    ["api"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Business metrics
FORECAST_REQUESTS = Counter(
    "weather_api_forecast_requests_total",
    "Total forecast requests by city",
    ["city_normalized", "status"],
)


def setup_metrics(app: FastAPI) -> Instrumentator:
    """Set up Prometheus metrics instrumentation.

    Args:
        app: FastAPI application instance.

    Returns:
        Configured Instrumentator instance.
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/metrics"],
        inprogress_name="weather_api_http_requests_inprogress",
        inprogress_labels=True,
    )

    instrumentator.instrument(app).expose(app, include_in_schema=False)

    return instrumentator
