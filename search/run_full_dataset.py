#!/usr/bin/env python3
"""
Run the full search pipeline on the entire dataset and persist all data locally.

- Loads skills from skills_scraper/data/skills_raw.jsonl
- Builds BM25 index (in memory, persisted implicitly via this script's state)
- Builds vector embeddings and caches to search/embeddings_cache.pkl
- Writes index metadata to search/data/index_meta.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Ensure we can import from search package
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import get_default_data_path
from search_engine import SkillSearchEngine


# Local data directory for all outputs
DATA_DIR = SCRIPT_DIR / "data"
INDEX_META_FILE = DATA_DIR / "index_meta.json"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Data directory: {DATA_DIR}")


def run_full_pipeline(skills_path: str = None):
    """
    Run the full pipeline on the entire dataset and save everything locally.
    
    Args:
        skills_path: Path to skills_raw.jsonl (default: auto)
    """
    ensure_data_dir()
    
    if skills_path is None:
        skills_path = get_default_data_path()
    
    cache_path = SCRIPT_DIR / "embeddings_cache.pkl"
    
    print("="*70)
    print("FULL DATASET PIPELINE - Loading and indexing all skills")
    print("="*70)
    print(f"Source: {skills_path}")
    print(f"Embeddings cache: {cache_path}\n")
    
    # Build search engine (loads data, BM25, vector cache, reranker)
    engine = SkillSearchEngine(skills_data_path=skills_path)
    n_skills = len(engine.skills)
    
    # Save index metadata
    meta = {
        "dataset_path": skills_path,
        "num_skills": n_skills,
        "embeddings_cache": str(cache_path),
        "embeddings_cache_exists": cache_path.exists(),
        "data_dir": str(DATA_DIR),
        "indexed_at": datetime.now().isoformat(),
    }
    with open(INDEX_META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Index metadata saved to: {INDEX_META_FILE}")

    print("\n" + "="*70)
    print("Pipeline complete. All data stored locally.")
    print("="*70)
    print(f"  Dataset:        {skills_path}")
    print(f"  Skills count:   {n_skills}")
    print(f"  Embeddings:     {cache_path}")
    print(f"  Index meta:     {INDEX_META_FILE}")
    print("")
    print("Run ad-hoc searches via CLI, e.g.:")
    print("  python cli.py \"react testing\" --top-k 3 --names-only")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build full-dataset indices and save metadata locally")
    parser.add_argument("--data-path", type=str, default=None, help="Path to skills_raw.jsonl")
    args = parser.parse_args()
    
    run_full_pipeline(skills_path=args.data_path)


if __name__ == "__main__":
    main()
