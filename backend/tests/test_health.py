"""Health endpoint tests."""

from __future__ import annotations


def test_liveness(client):
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
