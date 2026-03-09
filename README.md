# SkillRank

A hybrid search and recommendation engine for discovering AI agent skills from the [skills.sh](https://skills.sh) ecosystem. Users type a natural-language query describing what they want to accomplish, and SkillRank returns the most relevant skills ranked by a combination of semantic similarity and popularity signals.

Built as a final project for INFO376 (Search & Recommender Systems).

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Scrape the Data](#2-scrape-the-data)
  - [3. Set Up the Backend](#3-set-up-the-backend)
  - [4. Build the Vector Index](#4-build-the-vector-index)
  - [5. Start the Backend](#5-start-the-backend)
  - [6. Start the Frontend](#6-start-the-frontend)
- [API Reference](#api-reference)
- [Evaluation](#evaluation)
- [Running Tests](#running-tests)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [References](#references)

## Architecture Overview

```
                         skills.sh
                             |
                       [Scrapy Spider]
                             |
                     skills_raw.jsonl (981 skills)
                             |
                    [build_index.py]
                     /              \
            Embed (all-MiniLM-L6-v2)  Clean & normalize
                     \              /
                      Qdrant (vector DB)
                             |
        User Query --> [FastAPI Backend] --> [Next.js Frontend]
                        |          |
                  [Ollama LLM]  [Qdrant]
                  (query expansion)  (cosine similarity search)
```

## How It Works

### 1. Data Collection

A Scrapy spider visits three listing pages on skills.sh (top, trending, hot) and extracts every skill's name and link from embedded JavaScript data. It then visits each of the ~981 skill pages individually to collect the description, full documentation, weekly/total install counts, first-seen date, and GitHub URL. All records are saved to a single JSONL file.

### 2. Data Cleaning and Indexing

The raw data goes through normalization: install counts like `"4.2K"` are converted to numbers, date strings are parsed to ISO format, and HTML artifacts are stripped. Each skill's name and description are then fed through a sentence-transformer model (`all-MiniLM-L6-v2`) which converts the text into a 384-dimensional vector (embedding) that captures its semantic meaning. These vectors are stored in Qdrant, a vector database optimized for similarity search.

### 3. Query Expansion

When a user submits a query, it is first sent to a local Ollama LLM (`qwen3:0.6b`) that rewrites the casual query into more technical terms. For example, "I want to build a portfolio website" becomes a query mentioning React, Next.js, Tailwind, deployment, etc. This bridges the vocabulary gap between how users describe goals and how skills describe themselves. If Ollama is unavailable, the original query is used as-is.

### 4. Semantic Search

The (expanded) query is embedded using the same sentence-transformer model and sent to Qdrant, which returns the top candidates ranked by cosine similarity -- a measure of how close two vectors are in meaning, regardless of exact word overlap.

### 5. Result Explanation

After results are returned, the frontend makes a second call to Ollama to generate a per-skill explanation of why each skill matches the user's goal.

### 6. Conversation-Based Recommendations

An alternative mode reads recent user prompts from local Claude Code conversation history (`~/.claude/projects/`), embeds each prompt, queries Qdrant, and averages the scores to recommend skills based on what the user has been working on.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Data Collection | Python, Scrapy |
| Backend API | Python, FastAPI, Uvicorn |
| Vector Database | Qdrant (local Docker or Qdrant Cloud) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, 384 dimensions) |
| Query Expansion | Ollama (`qwen3:0.6b`, local) |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Testing | pytest (backend), ESLint (frontend) |

## Project Structure

```
SkillRank/
├── skills_scraper/              # Data collection
│   ├── skills_scraper/
│   │   ├── spiders/
│   │   │   └── skills_spider.py # Scrapy spider for skills.sh
│   │   ├── items.py             # Scrapy item schema
│   │   ├── settings.py          # Scrapy configuration
│   │   ├── pipelines.py         # Item processing pipeline
│   │   └── middlewares.py       # Request/response middlewares
│   ├── data/
│   │   └── skills_raw.jsonl     # Scraped dataset (981 skills)
│   └── scrapy.cfg
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py              # App entrypoint and startup lifecycle
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic settings from .env
│   │   │   ├── errors.py        # Custom exception classes and handlers
│   │   │   └── logging.py       # Logging configuration
│   │   ├── db/
│   │   │   └── qdrant.py        # Qdrant client wrapper
│   │   ├── services/
│   │   │   ├── embedder.py      # Sentence-transformer embedding service
│   │   │   ├── search_service.py    # Search orchestration
│   │   │   ├── ollama_service.py    # LLM query expansion and explanation
│   │   │   └── recommend_service.py # Conversation-based recommendations
│   │   ├── api/
│   │   │   ├── deps.py          # Dependency injection providers
│   │   │   └── v1/
│   │   │       ├── router.py    # API router composition
│   │   │       └── endpoints/
│   │   │           ├── search.py    # GET /api/v1/search
│   │   │           ├── explain.py   # POST /api/v1/explain
│   │   │           ├── recommend.py # POST /api/v1/recommend
│   │   │           └── health.py    # Liveness and readiness probes
│   │   └── schemas/
│   │       ├── search.py        # Search request/response models
│   │       ├── explain.py       # Explain request/response models
│   │       ├── recommend.py     # Recommend request/response models
│   │       └── common.py        # Shared response models
│   ├── scripts/
│   │   ├── build_index.py       # Build Qdrant vector index from JSONL
│   │   └── verify_index.py      # Verify index health with sample query
│   ├── tests/
│   │   ├── conftest.py          # Shared pytest fixtures
│   │   ├── test_health.py       # Health endpoint tests
│   │   └── test_search_contract.py # Search contract tests
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/                    # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Search page route
│   │   │   ├── recommend/
│   │   │   │   └── page.tsx     # Recommend page route
│   │   │   ├── layout.tsx       # Root layout
│   │   │   └── globals.css      # Global styles
│   │   ├── components/
│   │   │   ├── search-page.tsx          # Search UI component
│   │   │   ├── search-page.module.css
│   │   │   ├── recommend-page.tsx       # Recommend UI component
│   │   │   └── recommend-page.module.css
│   │   ├── lib/
│   │   │   ├── search-client.ts     # Search API client
│   │   │   ├── recommend-client.ts  # Recommend API client
│   │   │   └── explain-client.ts    # Explain API client
│   │   └── types/
│   │       ├── search.ts        # Search type definitions
│   │       └── recommend.ts     # Recommend type definitions
│   ├── package.json
│   ├── next.config.ts
│   └── .env.local.example
│
├── search/                      # Legacy standalone search engine
│   ├── data_loader.py           # JSONL loader and normalizer
│   ├── bm25_retriever.py        # BM25 keyword search
│   ├── vector_retriever.py      # Sentence-transformer vector search
│   ├── reranker.py              # Two-stage reranking algorithm
│   ├── search_engine.py         # Hybrid search orchestrator
│   ├── cli.py                   # Command-line interface
│   ├── app.py                   # Flask web app (legacy UI)
│   ├── run_full_dataset.py      # Full pipeline runner
│   ├── templates/
│   │   └── index.html           # Legacy web UI
│   ├── requirements.txt
│   └── README.md
│
├── test_cases/
│   └── ground_truth_top3.md     # Evaluation ground truth and results
│
├── .gitignore
└── README.md                    # This file
```

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10 - 3.12 | 3.13 is not supported by PyTorch |
| Node.js | 18+ | For the frontend |
| Docker | Any | For running Qdrant locally (or use Qdrant Cloud) |
| Ollama | Latest | Optional, for query expansion and explanations |

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/rpushkar9/SkillRank.git
cd SkillRank
```

### 2. Scrape the Data

The dataset (`skills_scraper/data/skills_raw.jsonl`) is already included in the repository. To re-scrape from scratch:

```bash
cd skills_scraper
pip install scrapy
scrapy crawl skills
```

This produces `data/skills_raw.jsonl` with ~981 skill records.

### 3. Set Up the Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

**Qdrant Cloud (recommended):**

Set `QDRANT_URL` and `QDRANT_API_KEY` in `.env` to your Qdrant Cloud cluster credentials.

**Local Qdrant via Docker:**

```bash
docker run --name skillrank-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

Leave `QDRANT_URL` empty in `.env` to use `localhost:6333`.

### 4. Build the Vector Index

```bash
cd backend
source .venv/bin/activate
python scripts/build_index.py --recreate
```

This reads the scraped data, generates embeddings with `all-MiniLM-L6-v2`, and upserts the vectors into Qdrant. Takes 1-2 minutes on first run.

Verify the index:

```bash
python scripts/verify_index.py --query "react testing" --limit 5
```

### 5. Start the Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Optionally start Ollama for query expansion:

```bash
ollama pull qwen3:0.6b
ollama serve
```

Verify the backend is running:

```bash
curl "http://127.0.0.1:8000/api/v1/search?q=react%20testing&k=3"
```

Interactive API docs are available at http://127.0.0.1:8000/docs.

### 6. Start the Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # only needed on first setup
npm run dev
```

Open http://localhost:3000 in your browser.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/search?q=<query>&k=<limit>` | Search skills by query. `q` is required, `k` defaults to 5 (max 20). |
| `POST` | `/api/v1/explain` | Generate per-skill explanations. Body: `{ "query": "...", "skills": [...] }` |
| `POST` | `/api/v1/recommend` | Recommend skills from Claude conversation history. Body: `{ "folder_path": "..." }` |
| `GET` | `/api/v1/health/live` | Liveness probe. Returns 200 if the server is running. |
| `GET` | `/api/v1/health/ready` | Readiness probe. Returns 200 if Qdrant and embedder are operational. |

### Example Search Response

```json
{
  "query": "react testing",
  "total": 3,
  "results": [
    {
      "skill_id": "skill-000354",
      "name": "typescript-react-reviewer",
      "description": "...",
      "skill_url": "https://github.com/...",
      "weekly_installs": 1500,
      "total_installs": 12000,
      "first_seen": "2026-01-15",
      "score": 0.5186
    }
  ],
  "took_ms": 42.15,
  "expanded_query": "React component testing, unit tests, Vitest, Jest...",
  "expand_ms": 320.5
}
```

## Evaluation

The search engine was evaluated against 10 manually curated ground-truth queries, each with an expected top-3 skill list.

| Metric | Value |
|--------|-------|
| Queries evaluated | 10 |
| Average Precision@3 | 0.20 |
| Queries with partial match (P@3 = 0.67) | 3 of 10 |
| Queries with no match (P@3 = 0.00) | 7 of 10 |

Full evaluation results and ground truth are in [`test_cases/ground_truth_top3.md`](test_cases/ground_truth_top3.md).

## Running Tests

**Backend:**

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v
```

**Frontend:**

```bash
cd frontend
npm run lint
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_URL` | *(empty)* | Qdrant Cloud endpoint. Leave empty for local Docker. |
| `QDRANT_API_KEY` | *(empty)* | Qdrant Cloud API key. Not needed for local Docker. |
| `QDRANT_HOST` | `localhost` | Host for local Qdrant. Ignored when `QDRANT_URL` is set. |
| `QDRANT_PORT` | `6333` | Port for local Qdrant. Ignored when `QDRANT_URL` is set. |
| `QDRANT_COLLECTION` | `skills` | Qdrant collection name. |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformer model for embeddings. |
| `EMBED_DIM` | `384` | Vector dimension (must match the model). |
| `SKILLS_JSONL_PATH` | `../skills_scraper/data/skills_raw.jsonl` | Path to the scraped skills data. |
| `DEFAULT_TOP_K` | `5` | Default number of results returned. |
| `MAX_TOP_K` | `20` | Maximum allowed value for `k`. |
| `QDRANT_TOP_N` | `50` | Internal Qdrant candidate pool size. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL. |
| `OLLAMA_MODEL` | `qwen3:0.6b` | Ollama model for query expansion. |
| `OLLAMA_ENABLED` | `true` | Set to `false` to disable query expansion. |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed CORS origins. |
| `SKIP_STARTUP_CHECKS` | `false` | Skip Qdrant/embedder checks on startup. |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | Backend API URL. |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Collection does not exist` | Run `python scripts/build_index.py --recreate` to build the index. |
| `Connection refused` on startup | Qdrant is not reachable. Check `QDRANT_URL` in `.env` or start the Docker container. |
| Frontend shows "Search request failed" | Backend is not running, or `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` is wrong. |
| `Module not found` errors | Virtual environment is not activated. Run `source .venv/bin/activate`. |
| Slow first query | The embedding model loads into memory on first request. Subsequent queries are fast. |
| PyTorch version conflict | Install PyTorch 2.4+ via conda: `conda install 'pytorch>=2.4' cpuonly -c pytorch -y` |
| NumPy 2.x incompatibility | Downgrade: `pip install "numpy<2.0.0"` |

## License

University project for INFO376 (Search & Recommender Systems).

## References

- Robertson, S. & Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond.* Foundations and Trends in Information Retrieval.
- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* [arXiv:1908.10084](https://arxiv.org/abs/1908.10084)
- Qdrant Documentation: [https://qdrant.tech/documentation/](https://qdrant.tech/documentation/)
- Ollama: [https://ollama.com](https://ollama.com)
- skills.sh: [https://skills.sh](https://skills.sh)
