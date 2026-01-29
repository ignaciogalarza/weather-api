"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from weather_api.config import settings
from weather_api.observability import (
    configure_logging,
    configure_tracing,
    instrument_fastapi,
    setup_metrics,
)
from weather_api.observability.middleware import RequestLoggingMiddleware
from weather_api.ratelimit import limiter
from weather_api.routes.auth import router as auth_router
from weather_api.routes.forecast import router as forecast_router
from weather_api.services.cache import close_cache, init_cache


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

    # Initialize Redis cache
    await init_cache()

    yield

    # Shutdown
    await close_cache()


app = FastAPI(
    title="Weather API",
    description="Weather forecast API",
    version=settings.service_version,
    lifespan=lifespan,
)

# Add rate limiter state
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": str(retry_after)},
    )


# Add observability middleware
app.add_middleware(RequestLoggingMiddleware)

# Setup Prometheus metrics
setup_metrics(app)

# Instrument FastAPI for tracing
instrument_fastapi(app)

# Include routers
app.include_router(auth_router)
app.include_router(forecast_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
