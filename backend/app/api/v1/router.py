"""Top-level API v1 router composition."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.recommend import router as recommend_router
from app.api.v1.endpoints.search import router as search_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(search_router)
api_router.include_router(recommend_router)
