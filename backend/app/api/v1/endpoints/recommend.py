"""Recommend endpoint: POST /api/v1/recommend."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.api.deps import get_recommend_service
from app.schemas.recommend import RecommendRequest, RecommendResponse
from app.services.recommend_service import RecommendService


router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("", response_model=RecommendResponse)
def recommend(
    body: RecommendRequest,
    recommend_service: RecommendService = Depends(get_recommend_service),
) -> RecommendResponse:
    """Recommend skills based on recent Claude conversation history."""
    start = time.perf_counter()
    prompts, results = recommend_service.recommend(body.folder_path)
    took_ms = round((time.perf_counter() - start) * 1000.0, 2)

    return RecommendResponse(
        folder_path=body.folder_path,
        prompts_used=prompts,
        results=results,
        took_ms=took_ms,
    )
