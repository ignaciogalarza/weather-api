"""Tests for the main application."""

from httpx import ASGITransport, AsyncClient

from weather_api.main import app


async def test_health_check() -> None:
    """Test health check endpoint returns healthy status."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
