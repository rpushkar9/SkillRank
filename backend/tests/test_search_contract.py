"""Search contract smoke test."""

from __future__ import annotations


def test_search_requires_query_param(client):
    response = client.get("/api/v1/search")
    assert response.status_code == 422
