#!/usr/bin/env python3
"""Build Qdrant vector index from skills JSONL."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from qdrant_client.models import PointStruct

# Ensure backend root is importable when running `python scripts/build_index.py`.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.qdrant import QdrantStore
from app.services.embedder import EmbedderService


def clean_text(text: str) -> str:
    """Normalize text by removing common HTML entities and whitespace noise."""
    if not text:
        return ""
    text = re.sub(r"&#x[0-9A-Fa-f]+;", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_install_count(value: str) -> int:
    """Convert install count text like '4.2K' or '1.5M' into integer."""
    if not value:
        return 0

    raw = str(value).strip().upper().replace(",", "")
    if not raw:
        return 0

    try:
        if raw.endswith("K"):
            return int(float(raw[:-1]) * 1_000)
        if raw.endswith("M"):
            return int(float(raw[:-1]) * 1_000_000)
        return int(float(raw))
    except ValueError:
        return 0


def parse_first_seen(value: str) -> str | None:
    """Normalize first_seen date string to ISO date when possible."""
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    for fmt in ("%b %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue

    return raw


def load_and_normalize(jsonl_path: Path) -> list[dict]:
    """Load raw JSONL data, normalize, and deduplicate by skill name.

    When duplicate names exist, the record with the highest total_installs
    is kept (most authoritative version).
    """
    seen: dict[str, dict] = {}

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            raw = json.loads(line)

            name = (raw.get("name") or "").strip()
            if not name:
                continue

            description = clean_text(raw.get("description") or "")
            example_usage = clean_text(raw.get("example_usage") or "")
            skill_url = (raw.get("skill_url") or "").strip()
            weekly_installs = parse_install_count(raw.get("weekly_installs") or "")

            try:
                total_installs = int(float(raw.get("total_installs") or 0))
            except (TypeError, ValueError):
                total_installs = 0

            first_seen = parse_first_seen(raw.get("first_seen") or "")

            existing = seen.get(name)
            if existing is not None and existing["total_installs"] >= total_installs:
                continue

            seen[name] = {
                "name": name,
                "description": description,
                "example_usage": example_usage,
                "skill_url": skill_url,
                "weekly_installs": weekly_installs,
                "total_installs": total_installs,
                "first_seen": first_seen,
            }

    records: list[dict] = []
    for point_id, (name, data) in enumerate(seen.items(), start=1):
        searchable_text = f"{name}. {data['description']} {data['example_usage']}".strip()
        records.append(
            {
                "point_id": point_id,
                "skill_id": f"skill-{point_id:06d}",
                **data,
                "searchable_text": searchable_text,
                "embedding_text": f"{name}. {data['description']}",
            }
        )

    return records


def chunked(items: list[dict], size: int) -> list[list[dict]]:
    """Yield fixed-size chunks."""
    return [items[i : i + size] for i in range(0, len(items), size)]


def build_index(recreate: bool, batch_size: int) -> None:
    """Main index build workflow."""
    settings = get_settings()
    jsonl_path = settings.skills_jsonl_abspath

    if not jsonl_path.exists():
        raise FileNotFoundError(f"Skills JSONL not found: {jsonl_path}")

    print(f"Loading skills from: {jsonl_path}")
    records = load_and_normalize(jsonl_path)
    print(f"Loaded records: {len(records)}")

    qdrant_store = QdrantStore(settings)
    qdrant_store.ensure_collection(recreate=recreate)

    embedder = EmbedderService(settings.embed_model)

    batches = chunked(records, batch_size)
    print(f"Indexing in {len(batches)} batches (batch_size={batch_size})")

    for batch_idx, batch in enumerate(batches, start=1):
        texts = [r["embedding_text"] for r in batch]
        vectors = embedder.embed_batch(texts)

        points: list[PointStruct] = []
        for record, vector in zip(batch, vectors):
            payload = {
                "skill_id": record["skill_id"],
                "name": record["name"],
                "description": record["description"],
                "example_usage": record["example_usage"],
                "skill_url": record["skill_url"],
                "weekly_installs": record["weekly_installs"],
                "total_installs": record["total_installs"],
                "first_seen": record["first_seen"],
                "searchable_text": record["searchable_text"],
            }

            points.append(
                PointStruct(
                    id=record["point_id"],
                    vector=vector,
                    payload=payload,
                )
            )

        qdrant_store.upsert_points(points)
        print(f"[{batch_idx}/{len(batches)}] Upserted {len(points)} points")

    indexed_count = qdrant_store.count_points()
    print(f"Done. Indexed points in collection '{settings.qdrant_collection}': {indexed_count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Qdrant index from skills JSONL")
    parser.add_argument("--recreate", action="store_true", help="Recreate collection before indexing")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding/upsert batch size")
    args = parser.parse_args()

    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")

    build_index(recreate=args.recreate, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
