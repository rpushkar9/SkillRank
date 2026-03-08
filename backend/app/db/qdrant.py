"""Qdrant wrapper to isolate vector DB operations from business logic."""

from __future__ import annotations

from typing import Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, ScoredPoint, VectorParams

from app.core.config import Settings


class QdrantStore:
    """Encapsulates collection management and similarity search."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.collection = settings.qdrant_collection
        if settings.qdrant_url:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key or None,
            )
        else:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key or None,
            )

    def is_healthy(self) -> bool:
        """Return True if Qdrant responds to basic metadata requests."""
        self.client.get_collections()
        return True

    def collection_exists(self) -> bool:
        """Check whether target collection exists."""
        try:
            return self.client.collection_exists(self.collection)
        except Exception:
            # Backward compatibility fallback.
            collections = self.client.get_collections().collections
            return any(c.name == self.collection for c in collections)

    def ensure_collection(self, recreate: bool = False) -> None:
        """Create collection if missing; optionally recreate from scratch."""
        exists = self.collection_exists()

        if recreate and exists:
            self.client.delete_collection(self.collection)
            exists = False

        if not exists:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.settings.embed_dim,
                    distance=Distance.COSINE,
                ),
            )

    def upsert_points(self, points: Sequence[PointStruct]) -> None:
        """Upsert a batch of vector points."""
        if not points:
            return
        self.client.upsert(
            collection_name=self.collection,
            points=points,
            wait=True,
        )

    def search(self, query_vector: list[float], limit: int) -> list[ScoredPoint]:
        """Run vector similarity search and return scored points."""
        response = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return response.points

    def count_points(self) -> int:
        """Return number of points in the collection."""
        result = self.client.count(collection_name=self.collection, exact=True)
        return int(result.count)
