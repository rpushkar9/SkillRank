"""Search orchestration service for query embedding + vector retrieval."""

from __future__ import annotations

from app.core.config import Settings
from app.core.errors import QueryValidationError, SearchExecutionError
from app.db.qdrant import QdrantStore
from app.schemas.search import SearchResult
from app.services.embedder import EmbedderService


class SearchService:
    """Runs semantic search against Qdrant and shapes API results."""

    def __init__(
        self,
        settings: Settings,
        qdrant_store: QdrantStore,
        embedder: EmbedderService,
    ):
        self.settings = settings
        self.qdrant_store = qdrant_store
        self.embedder = embedder

    def search(self, query: str, k: int) -> list[SearchResult]:
        """Execute semantic search and return top-k normalized results."""
        clean_query = query.strip()
        if not clean_query:
            raise QueryValidationError("Query must not be empty.")

        if k < 1 or k > self.settings.max_top_k:
            raise QueryValidationError(
                f"k must be between 1 and {self.settings.max_top_k}."
            )

        limit = max(k, self.settings.qdrant_top_n)

        try:
            query_vector = self.embedder.embed_query(clean_query)
            hits = self.qdrant_store.search(query_vector=query_vector, limit=limit)
        except Exception as exc:
            raise SearchExecutionError(f"Failed to execute vector search: {exc}") from exc

        results: list[SearchResult] = []
        for hit in hits:
            payload = hit.payload or {}
            result = SearchResult(
                skill_id=str(payload.get("skill_id", "")),
                name=str(payload.get("name", "")),
                description=str(payload.get("description", "")),
                skill_url=str(payload.get("skill_url", "")),
                weekly_installs=int(payload.get("weekly_installs", 0) or 0),
                total_installs=int(payload.get("total_installs", 0) or 0),
                first_seen=payload.get("first_seen"),
                score=float(hit.score or 0.0),
            )
            results.append(result)

        return results[:k]
