"""
Tests for the health check endpoint.
"""

import pytest


@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client):
    """GET /api/v1/health should return 200 with the expected structure."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["version"] is not None
    assert data["data"]["database"] in ("connected", "unavailable")
    assert data["data"]["ollama"] in ("connected", "unavailable")


@pytest.mark.asyncio
async def test_health_endpoint_response_structure(client):
    """Health response must follow the standard API envelope."""
    response = await client.get("/api/v1/health")
    data = response.json()

    # Envelope keys
    assert "status" in data
    assert "data" in data
    assert "message" in data

    # Health data keys
    health = data["data"]
    assert "status" in health
    assert "version" in health
    assert "database" in health
    assert "ollama" in health
