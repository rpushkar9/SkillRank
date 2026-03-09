"""Explain request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel


class SkillSummary(BaseModel):
    name: str
    description: str


class ExplainRequest(BaseModel):
    query: str
    skills: list[SkillSummary]


class ExplainResponse(BaseModel):
    lines: list[str]
    took_ms: float
