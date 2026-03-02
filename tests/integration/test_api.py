"""
Integration tests for API endpoints.
"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "URL Shortener API"


@pytest.mark.asyncio
async def test_shorten_url_invalid():
    """Test shortening invalid URL."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/shorten",
            json={"long_url": "not a url"},
        )
        # Should fail validation
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_analytics_not_found():
    """Test analytics for non-existent URL."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/analytics/notfound")
        assert response.status_code == 404
