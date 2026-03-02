# SkillRank: How It All Works

*Non-technical but thorough. Covers the full pipeline end-to-end and how to run everything.*

---

## The Big Picture

**skills.sh** is like an app store for AI agent capabilities — small packages called "skills" that extend what an AI (like Claude) can do. Skills have names like `react-testing`, `frontend-design`, `docker-deployment`. There are ~981 of them.

**SkillRank is a search engine for that catalog.** You type something like `"deploy a fastapi app to aws"` and it returns the 3 most relevant skills. It's not a simple "does the word match?" search — it's a hybrid system that combines keyword matching, semantic understanding, and popularity/recency signals.

---

## Data Source: skills.sh

Every skill on skills.sh has a detail page with:

| Field | Example |
|-------|---------|
| Name | `react-testing-best-practices` |
| Description | First sentence of the skill's README |
| Full content (`example_usage`) | The whole README |
| Weekly installs | `"4.2K"` = 4,200 |
| Total installs | `223000` |
| First seen | `"Jan 26, 2026"` or relative: `"12 days ago"` |
| URL | GitHub repo link |

The site is a Next.js app. The data isn't in plain HTML — it's embedded as JavaScript objects inside `<script>` tags. The scraper has to find and parse these JSON blobs.

---

## Step 1: Scraper — `skills_scraper/`

**What it does:** Visits skills.sh, extracts all skill data, saves it as a file.

**How:**
1. Starts at three pages: the main page, `/trending`, and `/hot`. Each shows up to 600 skills in a leaderboard.
2. Finds a JavaScript blob named `initialSkills` embedded in the page source — a JSON array of skill summaries.
3. For every skill, visits the individual detail page (e.g. `skills.sh/vercel-labs/react-performance`).
4. Extracts sidebar data (installs, first seen, URL) from one script chunk, and the full README from another.
5. Deduplicates by `source/skillId` so the same skill from two leaderboards is only scraped once.

**Output:** `skills_scraper/data/skills_raw.jsonl`

A JSONL file ("JSON Lines") — one JSON object per line:

```json
{
  "name": "find-skills",
  "description": "Find Skills This skill helps you discover...",
  "example_usage": "Find Skills This skill helps you discover... (full README)",
  "weekly_installs": "4.2K",
  "total_installs": "223000",
  "first_seen": "Jan 26, 2026",
  "skill_url": "https://github.com/example/skills"
}
```

**Known messy formats in raw data:**
- Installs are strings with K/M suffixes (`"4.2K"` not `4200`)
- Dates are sometimes relative (`"12 days ago"`, `"Today"`) not absolute
- Text has HTML entities (`&#x3C;` instead of `<`, `&amp;` instead of `&`)
- No stable unique ID per skill

---

## Step 2: Data Cleaning — `scripts/build_skills_clean.py`

**What it does:** Reads `skills_raw.jsonl`, fixes all the messy formats, writes `skills_clean.jsonl`.

**What it fixes:**

| Raw | Clean |
|-----|-------|
| `"4.2K"` | `4200` (integer) |
| `"12 days ago"` | `"2026-02-13"` (ISO date) |
| `"Today"` | today's date |
| `&#x3C;` | ` ` (HTML entities stripped) |
| (none) | `skill_id`: SHA1 hash of name + URL — stable unique ID |
| (none) | `name_norm`: lowercase, hyphens/spaces removed (`"front-end"` → `"frontend"`) |
| (none) | `searchable_text`: cleaned name + description + example_usage |

**How to run:**
```bash
python scripts/build_skills_clean.py
# Reads:  skills_scraper/data/skills_raw.jsonl
# Writes: skills_scraper/data/skills_clean.jsonl (981 rows, 0 parse failures)
```

> `skills_clean.jsonl` is gitignored — it's a generated file reproducible from `skills_raw.jsonl` in seconds.

---

## Step 3: Data Loading — `search/data_loader.py`

**What it does:** Reads either the raw or clean JSONL and returns a Python list of normalized dicts, ready for search modules.

**Key logic:**
- Handles both schemas: if `first_seen_date` exists (clean file), uses that; if only `first_seen` exists (raw), parses it on the fly
- Runs `clean_text()` to strip HTML entities (redundant for clean file, safe on raw)
- Builds `searchable_text = name + description + example_usage` for BM25

This is the **loading dock**: raw or clean data in, uniform format out. Every downstream module gets the same structure.

---

## Step 4: BM25 Retrieval — `search/bm25_retriever.py`

**What it does:** Classic keyword search. Given a query, find skills whose text has the most matching words.

**Analogy:** Like Ctrl+F across 981 documents, but smarter. BM25 (Best Matching 25) is the same algorithm that powers early Google. It rewards:
- Rare words that appear in few documents
- Documents where query words appear frequently
- Shorter documents (to avoid padding)

**Custom tokenizer:**
- Splits to lowercase words
- Removes stopwords (`"the"`, `"a"`, `"is"`, etc.)
- Removes single-character tokens
- Generates **bigrams**: adjacent words are concatenated, so `"front"` + `"end"` → `"frontend"`. A query `"frontend"` then matches a skill that writes `"front-end"` in its text.

**Indexes:** `name + description + example_usage`

**Output:** Top 25 skills with a raw BM25 score.

---

## Step 5: Vector Retrieval — `search/vector_retriever.py`

**What it does:** Semantic search. Finds skills that *mean the same thing* as the query, even if they use different words.

**Analogy:** Every skill and query is converted into a point in 384-dimensional space. Skills that are semantically similar end up close together. To search, you place your query in that space and find the nearest neighbors.

**Model:** `all-MiniLM-L6-v2` from sentence-transformers.

**Key details:**
- Only indexes `name + description` (not `example_usage`) — shorter text, more focused embedding
- Embeddings are computed once and **cached** to `search/embeddings_cache.pkl`. Delete the cache to force re-embedding.
- Cache is invalidated if the model or skill count changes.

**Output:** Top 25 skills with a cosine similarity score (0–1).

---

## Step 6: Merging — `search/search_engine.py`

**What it does:** Combines BM25 top-25 and vector top-25 into a single candidate pool.

**How:**
- **Union**: every skill from either list is included
- If a skill appears in both lists, it keeps both scores
- If it only appears in one, the other score is `None`
- Result: up to 50 candidates

**Why:** BM25 and vector each have blind spots:
- BM25 misses semantic matches (`"ship a container"` may not match a Docker skill if the word isn't used)
- Vector misses exact keyword matches (a skill named `pytest-best-practices` is obviously relevant to `"pytest"`)
- The union gives the reranker more material to work with.

---

## Step 7: Reranking — `search/reranker.py`

**What it does:** Takes 50 candidates and applies a two-stage formula to find the best answers.

### Stage 1 — Retrieval quality

1. Normalize BM25 scores to 0–1 (min-max across the candidate pool)
2. Normalize vector scores to 0–1
3. Treat `None` as 0
4. `combined_retrieval = 0.5 × bm25_norm + 0.5 × vector_norm`
5. **Title match bonus:**
   - Exact name match → +1.0
   - Query is a substring of the name → +0.5
   - Query word overlaps with name words → +0.3

**Stage 1 score** = `combined_retrieval × 0.5 + title_match × 0.1`

### Stage 2 — Popularity and recency (only if Stage 1 ≥ 0.4)

This prevents a viral but irrelevant skill from outranking a relevant but new one.

- **Recency**: exponential decay — a skill added yesterday gets ~1.0, 30 days ago ~0.5, a year ago ~0.03
- **Weekly installs**: log-scaled
- **Total installs**: log-scaled

**Final score** = `retrieval×0.5 + title_match×0.1 + recency×0.15 + weekly_installs×0.15 + total_installs×0.1`

### Weight summary

| Signal | Weight | Notes |
|--------|--------|-------|
| Retrieval (BM25 + vector) | 50% | Core relevance |
| Title match | 10% | Exact/substring bonus |
| Recency | 15% | Exponential decay over time |
| Weekly installs | 15% | Popularity, log-normalized |
| Total installs | 10% | Long-term popularity |

---

## Step 8: CLI — `search/cli.py`

```bash
python search/cli.py "deploy fastapi to aws" --top-k 3 --verbose --trace
```

| Flag | Effect |
|------|--------|
| `--top-k N` | Return N results (default: 3) |
| `--verbose` | Full score breakdown per result |
| `--names-only` | Just print skill names (useful for scripting) |
| `--data-path PATH` | Use clean JSONL instead of raw |
| `--trace` | Print BM25 top-10, vector top-10, merged count, reranked top-10 — for debugging |

---

## End-to-End: How to Run Everything

### 0. One-time setup

```bash
brew install uv
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r search/requirements.txt pytest
```

> conda is an alternative but uv is the recommended path on this machine.

### 1. (Optional) Build the clean data file

Only needed after re-scraping or if `skills_clean.jsonl` is missing:

```bash
python scripts/build_skills_clean.py
```

### 2. Build search indices

Builds BM25 index and computes + caches vector embeddings (~30–60s on first run):

```bash
python search/run_full_dataset.py

# Or use clean file:
python search/run_full_dataset.py --data-path skills_scraper/data/skills_clean.jsonl
```

### 3. Run a query

```bash
python search/cli.py "react testing"
python search/cli.py "deploy fastapi to aws" --top-k 5 --verbose
python search/cli.py "frontend design" --names-only
python search/cli.py "docker kubernetes" --trace
python search/cli.py "react testing" --data-path skills_scraper/data/skills_clean.jsonl --top-k 5 --verbose
```

### 4. Run tests

```bash
# Tokenizer unit tests (fast, no ML needed)
cd search && python -m pytest -v test_tokenize.py

# Data cleaner unit tests
cd .. && python -m pytest scripts/test_build_skills_clean.py -v
```

### 5. Re-scrape (only for fresh data)

```bash
cd skills_scraper
scrapy crawl skills
cd ..
# Then re-run steps 1–2
```

---

## File Map

```
SkillRank/
├── skills_scraper/
│   ├── skills_scraper/spiders/skills_spider.py  ← Scrapy spider
│   └── data/
│       ├── skills_raw.jsonl     ← raw scraped data (committed, 8 MB)
│       └── skills_clean.jsonl   ← cleaned data (generated, gitignored, 16 MB)
│
├── scripts/
│   ├── build_skills_clean.py        ← raw → clean transformer
│   └── test_build_skills_clean.py   ← unit tests for the cleaner
│
└── search/
    ├── data_loader.py      ← load + normalize JSONL → Python dicts
    ├── bm25_retriever.py   ← keyword search (BM25Okapi)
    ├── vector_retriever.py ← semantic search (sentence-transformers)
    ├── search_engine.py    ← merge BM25 + vector → candidate pool
    ├── reranker.py         ← two-stage scoring
    ├── cli.py              ← command-line interface
    ├── run_full_dataset.py ← build indices + cache (run once)
    └── test_tokenize.py    ← unit tests for tokenize()
```

---

## Current State

- ~981 skills indexed
- Average Precision@3 on the 10-query eval set is **0.20** (see `test_cases/ground_truth_top3.md`)
- Improving retrieval quality is the primary open problem
