#!/usr/bin/env python3
"""Verify Qdrant index status and run a sample search."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure backend root is importable when running `python scripts/verify_index.py`.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.qdrant import QdrantStore
from app.services.embedder import EmbedderService


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify indexed skill vectors in Qdrant")
    parser.add_argument("--query", type=str, default="react testing", help="Sample query")
    parser.add_argument("--limit", type=int, default=5, help="How many sample hits to print")
    args = parser.parse_args()

    settings = get_settings()
    store = QdrantStore(settings)

    print(f"Qdrant collection: {settings.qdrant_collection}")
    print(f"Collection exists: {store.collection_exists()}")

    if not store.collection_exists():
        raise RuntimeError("Collection does not exist. Run build_index.py first.")

    count = store.count_points()
    print(f"Indexed point count: {count}")

    embedder = EmbedderService(settings.embed_model)
    query_vec = embedder.embed_query(args.query)
    hits = store.search(query_vector=query_vec, limit=args.limit)

    print(f"\nSample query: {args.query}")
    if not hits:
        print("No hits found.")
        return

    for idx, hit in enumerate(hits, start=1):
        payload = hit.payload or {}
        name = payload.get("name", "")
        skill_id = payload.get("skill_id", "")
        print(f"{idx}. {name} ({skill_id}) score={float(hit.score or 0.0):.4f}")


if __name__ == "__main__":
    main()
