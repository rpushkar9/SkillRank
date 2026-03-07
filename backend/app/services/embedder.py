"""Embedding service wrapping sentence-transformers model lifecycle."""

from __future__ import annotations

from sentence_transformers import SentenceTransformer


class EmbedderService:
    """Loads a sentence-transformer once and exposes embed APIs."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text: str) -> list[float]:
        """Embed one query string into vector representation."""
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts for indexing."""
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()
