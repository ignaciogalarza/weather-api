"""FastAPI application entry point."""

from fastapi import FastAPI

from weather_api.routes.forecast import router as forecast_router

app = FastAPI(
    title="Weather API",
    description="Weather forecast API",
    version="0.1.0",
)

app.include_router(forecast_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
