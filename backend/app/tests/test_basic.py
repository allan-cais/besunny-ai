"""
Basic tests for BeSunny.ai Python backend.
"""

import pytest
from fastapi.testclient import TestClient

from ..main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "service" in data
    assert "version" in data


def test_api_v1_health(client):
    """Test API v1 health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "v1"
    assert "endpoints" in data


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/health")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
