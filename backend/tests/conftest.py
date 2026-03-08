"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Keep tests lightweight by disabling heavy startup checks if needed.
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("SKIP_STARTUP_CHECKS", "true")

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
