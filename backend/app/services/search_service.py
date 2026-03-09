"""Search orchestration service for query embedding + vector retrieval."""

from __future__ import annotations

import time

from app.core.config import Settings
from app.core.errors import QueryValidationError, SearchExecutionError
from app.db.qdrant import QdrantStore
from app.schemas.search import SearchResult
from app.services.embedder import EmbedderService
from app.services.ollama_service import OllamaService


class SearchService:
    """Runs semantic search against Qdrant and shapes API results."""

    def __init__(
        self,
        settings: Settings,
        qdrant_store: QdrantStore,
        embedder: EmbedderService,
        ollama: OllamaService,
    ):
        self.settings = settings
        self.qdrant_store = qdrant_store
        self.embedder = embedder
        self.ollama = ollama

    def search(
        self, query: str, k: int
    ) -> tuple[list[SearchResult], str | None, float | None, float]:
        """Execute semantic search.

        Returns (results, expanded_query, expand_ms, search_ms).
        expand_ms is None when Ollama was skipped or produced the same text.
        """
        clean_query = query.strip()
        if not clean_query:
            raise QueryValidationError("Query must not be empty.")

        if k < 1 or k > self.settings.max_top_k:
            raise QueryValidationError(
                f"k must be between 1 and {self.settings.max_top_k}."
            )

        # Step 1: query expansion via Ollama
        t0 = time.perf_counter()
        if self.settings.ollama_enabled:
            expanded = self.ollama.expand_query(clean_query)
        else:
            expanded = clean_query
        expand_elapsed = (time.perf_counter() - t0) * 1000.0
        expanded_out = expanded if expanded != clean_query else None
        expand_ms = round(expand_elapsed, 1) if expanded_out else None

        # Step 2: embed + Qdrant search
        limit = max(k, self.settings.qdrant_top_n)
        t1 = time.perf_counter()
        try:
            query_vector = self.embedder.embed_query(expanded)
            hits = self.qdrant_store.search(query_vector=query_vector, limit=limit)
        except Exception as exc:
            raise SearchExecutionError(f"Failed to execute vector search: {exc}") from exc
        search_ms = round((time.perf_counter() - t1) * 1000.0, 1)

        results: list[SearchResult] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(SearchResult(
                skill_id=str(payload.get("skill_id", "")),
                name=str(payload.get("name", "")),
                description=str(payload.get("description", "")),
                skill_url=str(payload.get("skill_url", "")),
                weekly_installs=int(payload.get("weekly_installs", 0) or 0),
                total_installs=int(payload.get("total_installs", 0) or 0),
                first_seen=payload.get("first_seen"),
                score=float(hit.score or 0.0),
            ))

        return results[:k], expanded_out, expand_ms, search_ms
