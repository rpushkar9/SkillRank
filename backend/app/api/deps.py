"""Dependency providers for FastAPI endpoints."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.db.qdrant import QdrantStore
from app.services.embedder import EmbedderService
from app.services.recommend_service import RecommendService
from app.services.search_service import SearchService


@lru_cache
def get_qdrant_store() -> QdrantStore:
    """Return cached Qdrant store instance."""
    settings = get_settings()
    return QdrantStore(settings)


@lru_cache
def get_embedder() -> EmbedderService:
    """Return cached embedder service instance."""
    settings = get_settings()
    return EmbedderService(settings.embed_model)


@lru_cache
def get_search_service() -> SearchService:
    """Return cached search service instance."""
    settings: Settings = get_settings()
    return SearchService(
        settings=settings,
        qdrant_store=get_qdrant_store(),
        embedder=get_embedder(),
    )


@lru_cache
def get_recommend_service() -> RecommendService:
    """Return cached recommend service instance."""
    settings: Settings = get_settings()
    return RecommendService(
        settings=settings,
        qdrant_store=get_qdrant_store(),
        embedder=get_embedder(),
    )
