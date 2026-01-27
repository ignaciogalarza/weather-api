"""FastAPI application entry point."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from weather_api.observability import (
    configure_logging,
    configure_tracing,
    instrument_fastapi,
    setup_metrics,
)
from weather_api.observability.middleware import RequestLoggingMiddleware
from weather_api.routes.forecast import router as forecast_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler for startup/shutdown."""
    # Startup
    json_logs = os.getenv("LOG_FORMAT", "json") == "json"
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(json_format=json_logs, log_level=log_level)

    # Configure tracing (will use OTEL_EXPORTER_OTLP_ENDPOINT env var if set)
    configure_tracing(
        service_name="weather-api",
        console_export=os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true",
    )

    yield

    # Shutdown (cleanup if needed)


app = FastAPI(
    title="Weather API",
    description="Weather forecast API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add observability middleware
app.add_middleware(RequestLoggingMiddleware)

# Setup Prometheus metrics
setup_metrics(app)

# Instrument FastAPI for tracing
instrument_fastapi(app)

# Include routers
app.include_router(forecast_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
