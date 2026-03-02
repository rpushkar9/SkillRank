# Repo Map (SkillRank)

Last updated: 2026-02-23

## Directory tree (top 3 levels)

```
SkillRank/
├── docs/
├── search/
├── scripts/
├── skills_scraper/
│   ├── data/
│   └── skills_scraper/
│       └── spiders/
└── test_cases/
```

## Where data lives

- **Scraped skills (JSONL):** `skills_scraper/data/skills_raw.jsonl`  
  One JSON object per line; produced by the Scrapy feed when the scraper is run from `skills_scraper/`.

## Where search code lives

| File | Role |
|------|------|
| `search/search_engine.py` | Main orchestrator: loads data, runs BM25 + vector retrieval, merge, rerank. |
| `search/bm25_retriever.py` | BM25 keyword retrieval. |
| `search/vector_retriever.py` | Semantic retrieval (sentence-transformers, embeddings). |
| `search/reranker.py` | Two-stage scoring and reranking (relevance + popularity boost). |
| `search/data_loader.py` | Load/parse/normalize `skills_raw.jsonl`. |
| `search/cli.py` | CLI entrypoint for running searches. |
| `search/run_full_dataset.py` | Build indices on full dataset and persist cache/metadata. |

Output paths used by search: `search/data/` (e.g. `search/data/index_meta.json`); default skills path is `skills_scraper/data/skills_raw.jsonl`.

## How to run locally

### Scraper (to (re)generate `skills_raw.jsonl`)

```bash
cd skills_scraper
scrapy crawl <spider_name>
```

(Spider name is in `skills_scraper/skills_scraper/spiders/`; run `scrapy list` in that directory to see it.)

### Search (recommended: conda)

```bash
# One-time setup
conda create -n skills python=3.10 -y
conda activate skills
conda install pytorch cpuonly -c pytorch -y

cd search
pip install -r requirements.txt
```

**First run (build indices + cache embeddings):**

```bash
cd search
python run_full_dataset.py
```

**Query from CLI:**

```bash
cd search
python cli.py "your search query"
python cli.py "react testing" --top-k 5 --verbose
```

**Optional:** use a custom skills file:

```bash
python cli.py "query" --data-path /path/to/skills_raw.jsonl
python run_full_dataset.py --data-path /path/to/skills_raw.jsonl
```
