"""Health endpoints for liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.common import HealthResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
def live() -> HealthResponse:
    """Liveness probe: process is running."""
    return HealthResponse(status="ok", detail="process is alive")


@router.get("/ready", response_model=HealthResponse)
def ready(request: Request) -> HealthResponse:
    """Readiness probe: critical dependencies are available."""
    is_ready = bool(getattr(request.app.state, "is_ready", False))
    detail = str(getattr(request.app.state, "ready_detail", "not_initialized"))

    if not is_ready:
        raise HTTPException(status_code=503, detail=detail)

    return HealthResponse(status="ok", detail=detail)
