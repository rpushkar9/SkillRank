# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillRank is a hybrid skill-recommendation search engine. Given a natural-language query, it returns the top-3 most relevant Claude skills from a scraped dataset. The pipeline is: BM25 + vector retrieval → merge → two-stage rerank.

---

## Environment Setup

Two equivalent paths — pick one.

**uv (recommended, no conda needed):**
```bash
brew install uv
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r search/requirements.txt pytest
```

**conda (if you need PyTorch GPU or already use conda):**
```bash
conda create -n skills python=3.10 -y
conda activate skills
conda install pytorch cpuonly -c pytorch -y
pip install -r search/requirements.txt
```

> `torch` is intentionally excluded from `requirements.txt` (conda installs it separately). With uv, `sentence-transformers` pulls in a CPU-only torch automatically.

---

## Common Commands

**Build indices + cache embeddings (first run or after data changes):**
```bash
python search/run_full_dataset.py
```

**Run a search query:**
```bash
python search/cli.py "your search query"
python search/cli.py "react testing" --top-k 5 --verbose
python search/cli.py "deployment" --names-only
```

**Run unit tests (no full ML stack required):**
```bash
cd search && python -m pytest -v test_tokenize.py
```

**Re-scrape skills data:**
```bash
cd skills_scraper
scrapy list          # see spider name
scrapy crawl <spider_name>
```

**Run the dataset analysis script:**
```bash
python scripts/analyze_skills_jsonl.py
```

Unit tests for `tokenize()` live in `search/test_tokenize.py` (run with pytest). End-to-end evaluation is manual via `test_cases/ground_truth_top3.md` (10 queries, Precision@3).

---

## Architecture

### Data flow

```
skills_scraper/data/skills_raw.jsonl
        │
        ▼
search/data_loader.py       ← load_skills() normalizes JSONL, builds searchable_text
        │
        ├──► search/bm25_retriever.py   ← BM25Okapi on name+description+example_usage
        │
        └──► search/vector_retriever.py ← sentence-transformers (all-MiniLM-L6-v2)
                                          embeds name+description only; caches to
                                          search/embeddings_cache.pkl
        │
        ▼
search/search_engine.py     ← SkillSearchEngine._merge_results()
                              Union of BM25+vector; each score retained separately
        │
        ▼
search/reranker.py          ← Reranker.rerank()
                              Stage 1: combined_retrieval (w_bm25=0.5 * bm25_norm + w_vec=0.5 * vector_norm)
                                       + title_match; keep top 50
                              Stage 2: if combined_retrieval ≥ 0.4, add recency + installs boost
        │
        ▼
search/cli.py               ← CLI entrypoint
```

### Key design decisions

- **Merge strategy:** Union of both retrieval sets; `bm25_score` and `vector_score` are tracked separately on each candidate (either may be `None`). The reranker normalizes them independently and combines as `0.5*bm25_norm + 0.5*vec_norm`.
- **Retrieval text differs by retriever:** BM25 indexes `name + description + example_usage`; vector embeddings use `name + description` only.
- **Reranker weights** (all tunable in `reranker.py`): retrieval=0.5, title_match=0.1, recency=0.15, weekly_installs=0.15, total_installs=0.1; popularity boost only fires when `combined_retrieval >= 0.4`.
- **Embeddings are cached** in `search/embeddings_cache.pkl`; delete it to force re-embedding after data changes.
- **All search modules use relative imports** — they must be run from the `search/` directory.

### Normalized skill dict fields

`name`, `description`, `example_usage`, `skill_url`, `weekly_installs` (float), `total_installs` (float), `first_seen` (datetime), `first_seen_str` (raw string), `searchable_text`.

---

## Current State / Known Issues

- Average Precision@3 on the 10-query eval set is **0.20** (see `test_cases/ground_truth_top3.md`). Improving retrieval quality is the primary open problem.
- The merge format is `{"name", "bm25_score", "vector_score"}` dicts (no max-merge); BM25 and vector scores are normalized independently in the reranker.
