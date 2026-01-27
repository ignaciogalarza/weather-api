"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="Weather API",
    description="Weather forecast API",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
