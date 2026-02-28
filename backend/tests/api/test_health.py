"""
Test health endpoint.
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "PPSC" in data["app"]


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data
