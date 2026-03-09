"""Explain endpoint: POST /api/v1/explain."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from app.api.deps import get_ollama_service
from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services.ollama_service import OllamaService


router = APIRouter(prefix="/explain", tags=["explain"])


@router.post("", response_model=ExplainResponse)
def explain(
    body: ExplainRequest,
    ollama: OllamaService = Depends(get_ollama_service),
) -> ExplainResponse:
    """Generate per-skill explanations for why the skills match the user's goal."""
    start = time.perf_counter()
    skill_tuples = [(s.name, s.description) for s in body.skills]
    lines = ollama.explain_results(body.query, skill_tuples)
    took_ms = round((time.perf_counter() - start) * 1000.0, 2)
    return ExplainResponse(lines=lines, took_ms=took_ms)
