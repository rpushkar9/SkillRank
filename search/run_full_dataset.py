#!/usr/bin/env python3
"""
Run the full search pipeline on the entire dataset and persist all data locally.

- Loads skills from skills_scraper/data/skills_raw.jsonl
- Builds BM25 index (in memory, persisted implicitly via this script's state)
- Builds vector embeddings and caches to search/embeddings_cache.pkl
- Runs a set of queries and saves results to search/data/
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
RESULTS_FILE = DATA_DIR / "search_results.jsonl"
INDEX_META_FILE = DATA_DIR / "index_meta.json"
QUERIES_FILE = DATA_DIR / "queries_run.json"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Data directory: {DATA_DIR}")


def run_full_pipeline(skills_path: str = None, run_queries: bool = True):
    """
    Run the full pipeline on the entire dataset and save everything locally.
    
    Args:
        skills_path: Path to skills_raw.jsonl (default: auto)
        run_queries: If True, run example queries and save results
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
    
    if not run_queries:
        print("\nPipeline ready. Re-run without --no-queries to run and save query results.")
        return
    
    print("\nRunning queries and saving results to data/ ...")
    # Representative queries to run
    queries = [
        "react testing",
        "python django",
        "deployment kubernetes",
        "api design",
        "testing framework",
        "database",
        "frontend css",
        "security",
        "docker",
        "documentation",
    ]
    
    all_results = []
    
    with open(RESULTS_FILE, "w", encoding="utf-8") as out:
        for query in queries:
            results = engine.search(query, top_k=3, verbose=False)
            record = {
                "query": query,
                "top_k": 3,
                "results": [
                    {
                        "rank": i + 1,
                        "name": r["name"],
                        "final_score": r["final_score"],
                        "description": r["description"][:200] + "..." if len(r["description"]) > 200 else r["description"],
                        "skill_url": r["skill_url"],
                        "weekly_installs": r["weekly_installs"],
                        "total_installs": r["total_installs"],
                        "first_seen": r["first_seen"],
                        "score_breakdown": r["score_breakdown"],
                    }
                    for i, r in enumerate(results)
                ],
            }
            all_results.append(record)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"  Query: '{query}' -> top 3 saved")
    
    print(f"\nResults written to: {RESULTS_FILE}")
    
    # Save query list and summary
    queries_summary = {
        "queries": queries,
        "results_file": str(RESULTS_FILE),
        "run_at": datetime.now().isoformat(),
        "num_queries": len(queries),
    }
    with open(QUERIES_FILE, "w", encoding="utf-8") as f:
        json.dump(queries_summary, f, indent=2)
    print(f"Queries summary: {QUERIES_FILE}")
    
    print("\n" + "="*70)
    print("Pipeline complete. All data stored locally.")
    print("="*70)
    print(f"  Dataset:        {skills_path}")
    print(f"  Skills count:   {n_skills}")
    print(f"  Embeddings:     {cache_path}")
    print(f"  Index meta:     {INDEX_META_FILE}")
    print(f"  Query results:  {RESULTS_FILE}")
    print(f"  Queries list:   {QUERIES_FILE}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run full search pipeline and save data locally")
    parser.add_argument("--data-path", type=str, default=None, help="Path to skills_raw.jsonl")
    parser.add_argument("--no-queries", action="store_true", help="Only build indices, do not run queries")
    args = parser.parse_args()
    
    run_full_pipeline(skills_path=args.data_path, run_queries=not args.no_queries)


if __name__ == "__main__":
    main()
