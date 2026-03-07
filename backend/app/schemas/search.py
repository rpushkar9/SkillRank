"""Search request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """One ranked skill result."""

    skill_id: str
    name: str
    description: str = ""
    skill_url: str = ""
    weekly_installs: int = 0
    total_installs: int = 0
    first_seen: str | None = None
    score: float = Field(..., description="Vector similarity score from Qdrant")


class SearchResponse(BaseModel):
    """Search response payload."""

    query: str
    total: int
    results: list[SearchResult]
    took_ms: float
