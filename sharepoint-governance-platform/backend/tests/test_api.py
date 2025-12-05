"""
Integration tests for API endpoints
"""
import pytest
from fastapi import status


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"


def test_api_root(client):
    """Test API root endpoint"""
    response = client.get("/api/v1/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "endpoints" in data
    assert "auth" in data["endpoints"]
