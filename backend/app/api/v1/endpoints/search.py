"""Search endpoint exposing semantic retrieval to clients."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_search_service
from app.core.config import Settings, get_settings
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService


router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    q: Annotated[str, Query(min_length=1, description="User search query")],
    k: Annotated[
        int | None, Query(ge=1, le=100, description="Number of results")
    ] = None,
    search_service: SearchService = Depends(get_search_service),
    settings: Settings = Depends(get_settings),
) -> SearchResponse:
    """Search skills using vector retrieval from Qdrant."""
    if k is None:
        k = settings.default_top_k

    if k > settings.max_top_k:
        k = settings.max_top_k

    start = time.perf_counter()
    results = search_service.search(query=q, k=k)
    took_ms = (time.perf_counter() - start) * 1000.0

    return SearchResponse(
        query=q,
        total=len(results),
        results=results,
        took_ms=round(took_ms, 2),
    )
