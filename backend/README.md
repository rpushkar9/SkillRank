# SkillRank Backend

Semantic skill search API built with FastAPI and Qdrant. A user types a query on the frontend, the backend embeds it into a 384-dimensional vector, and Qdrant returns the most similar skills by cosine similarity.

```
Frontend (Next.js)  -->  GET /api/v1/search?q=...  -->  FastAPI  -->  Qdrant
```

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10 - 3.12 | 3.13 is not supported by PyTorch |
| Node.js | 18+ | For the frontend |
| npm | 9+ | Comes with Node.js |
| Docker | Any | Only if running Qdrant locally instead of cloud |

---

## Step 1: Set Up the Backend

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 2: Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and configure your Qdrant connection. Pick one of the two options below.

**Option A: Qdrant Cloud (recommended)**

1. Create a free account at https://cloud.qdrant.io
2. Create a cluster and generate an API key
3. Set these in `.env`:

```
QDRANT_URL=https://<your-cluster-id>.cloud.qdrant.io:6333
QDRANT_API_KEY=<your-api-key>
```

**Option B: Local Qdrant via Docker**

```bash
docker run --name skillrank-qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

Then in `.env`, leave `QDRANT_URL` empty so the client falls back to `localhost:6333`:

```
QDRANT_URL=
QDRANT_API_KEY=
```

All other defaults in `.env.example` are correct and do not need changes.

---

## Step 3: Build the Vector Index

This reads the scraped skills from `skills_scraper/data/skills_raw.jsonl`, embeds them with the `all-MiniLM-L6-v2` model, deduplicates by skill name, and upserts the vectors into Qdrant.

```bash
python scripts/build_index.py --recreate
```

The first run downloads the embedding model (~80 MB) and takes 1-2 minutes. Expected output:

```
Loaded records: 921
Indexing in 15 batches (batch_size=64)
...
Done. Indexed points in collection 'skills': 921
```

Verify the index is healthy:

```bash
python scripts/verify_index.py --query "react testing" --limit 5
```

You should see 5 results with cosine similarity scores, no warnings.

---

## Step 4: Start the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

The server runs startup checks (Qdrant connectivity and embedder model loading). Once you see `Application startup complete`, the API is ready.

Quick smoke test in another terminal:

```bash
curl "http://127.0.0.1:8000/api/v1/search?q=react%20testing&k=3"
```

You can also open http://127.0.0.1:8000/docs for the interactive Swagger UI.

---

## Step 5: Start the Frontend

Open a new terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

If this is your first time setting up the frontend (no `frontend/.env.local` file exists), copy the template first:

```bash
cp .env.local.example .env.local
```

The default `.env.local` points to `http://127.0.0.1:8000`, which matches the backend. No changes needed if you kept the default port.

Open http://localhost:3000 in your browser, type a query, and you should see ranked skill results.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/search?q=<query>&k=<limit>` | Search skills. `q` is required, `k` defaults to 5 (max 20). |
| `GET` | `/api/v1/health/live` | Returns 200 if the server is running. |
| `GET` | `/api/v1/health/ready` | Returns 200 if Qdrant and the embedder are operational. |

### Example Response

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
  "took_ms": 42.15
}
```

---

## Running Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

---

## Troubleshooting

**"Collection does not exist"**
You have not built the index yet. Run `python scripts/build_index.py --recreate`.

**"Connection refused" or startup fails with 503**
Qdrant is not reachable. Check that your `QDRANT_URL` and `QDRANT_API_KEY` in `.env` are correct, or that your Docker container is running.

**"Module not found" errors**
Your virtual environment is not activated. Run `source .venv/bin/activate`.

**Frontend shows "Search request failed"**
The backend is not running, or the frontend `.env.local` points to the wrong URL. Confirm the backend is up on port 8000 and that `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` is set in `frontend/.env.local`.

**Slow first query**
The embedding model loads into memory on the first request after startup. Subsequent queries are fast.

---

## Environment Variables Reference

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
| `QDRANT_TOP_N` | `50` | Number of candidates Qdrant retrieves internally before returning top-k. |
| `CORS_ALLOW_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed CORS origins. |
| `SKIP_STARTUP_CHECKS` | `false` | Skip Qdrant/embedder checks on startup (for testing). |
