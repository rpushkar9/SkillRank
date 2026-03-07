"""Shared API response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard API error payload."""

    error: str
    detail: str


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str
    detail: str
