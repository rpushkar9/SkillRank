"""Recommender request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.search import SearchResult


class RecommendRequest(BaseModel):
    """Request body for the recommend endpoint."""

    folder_path: str


class RecommendResponse(BaseModel):
    """Recommend response payload."""

    folder_path: str
    prompts_used: list[str]
    results: list[SearchResult]
    took_ms: float
