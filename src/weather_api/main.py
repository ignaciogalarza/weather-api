"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from weather_api.config import settings
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
    configure_logging(
        json_format=settings.log_format == "json",
        log_level=settings.log_level,
    )

    configure_tracing(
        service_name=settings.service_name,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
        console_export=settings.otel_console_export,
    )

    yield

    # Shutdown (cleanup if needed)


app = FastAPI(
    title="Weather API",
    description="Weather forecast API",
    version=settings.service_version,
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
