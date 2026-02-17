# Skills Hybrid Search and Ranking System

A production-ready hybrid retrieval system that combines **BM25 keyword search** and **semantic vector search** to recommend the most relevant skills from a dataset of 981 skills.

## Features

- **🔍 Hybrid Retrieval**: Combines BM25 (keyword) and sentence-transformers (semantic) search
- **🎯 Two-Stage Smart Reranking**:
  - **Stage 1**: Rank by relevance (retrieval 50% + title match 10%)
  - **Stage 2**: Apply popularity boost (recency 15% + weekly installs 15% + total installs 10%) only to highly relevant results (retrieval score ≥ threshold)
- **⚡ Fast Performance**: Embedding caching for instant subsequent searches
- **📊 Transparent Scoring**: Detailed score breakdowns for debugging
- **🎨 Clean CLI**: Easy-to-use command-line interface

## Architecture

```
Query → [BM25 Retrieval (top 25)]   ─┐
                                     ├→ [Merge & Deduplicate] → [Rerank] → Top 3 Results
Query → [Vector Retrieval (top 25)] ─┘
```

### Two-Stage Scoring Formula

**Stage 1: Relevance Ranking**
```python
stage1_score = (
    retrieval_score * 0.5 +      # BM25/vector similarity (50%)
    title_match_score * 0.1      # Exact/partial name match (10%)
)
```

**Stage 2: Popularity Boost (only if retrieval_score ≥ threshold)**
```python
if retrieval_score >= 0.4:  # Relevance threshold
    final_score = stage1_score + (
        recency_score * 0.15 +           # Days since first_seen (15%)
        weekly_installs_score * 0.15 +   # Log-normalized weekly installs (15%)
        total_installs_score * 0.1       # Log-normalized total installs (10%)
    )
else:
    final_score = stage1_score  # No popularity boost for low-relevance results
```

This ensures that only truly relevant results benefit from popularity signals, preventing popular but irrelevant skills from ranking highly.

## Installation

### 1. Install Dependencies

```bash
cd search
pip install -r requirements.txt
```

**Dependencies:**
- `rank-bm25==0.2.2` - BM25 keyword search
- `sentence-transformers==2.3.1` - Semantic embeddings
- `numpy==1.24.3` - Numerical operations
- `scikit-learn==1.3.2` - Similarity metrics
- `pandas==2.1.4` - Data handling
- `python-dateutil==2.8.2` - Date parsing

### 2. First Run (Embedding Generation)

On the first run, the system will download the sentence-transformer model (`all-MiniLM-L6-v2`) and generate embeddings for all skills. This takes 2-3 minutes but only happens once:

```bash
python cli.py "test query"
```

Embeddings are cached in `embeddings_cache.pkl` for instant subsequent searches.

### 3. Run Full Dataset and Save Data Locally

To run the entire pipeline on the full dataset (981 skills) and persist all data locally:

```bash
cd search
pip install -r requirements.txt   # if not already installed
python run_full_dataset.py
```

**What gets stored locally:**

| Path | Description |
|------|-------------|
| `search/data/` | Output directory (created automatically) |
| `search/data/index_meta.json` | Index metadata (dataset path, skill count, cache path, timestamp) |
| `search/data/search_results.jsonl` | One JSON object per line: query + top-3 results with scores |
| `search/data/queries_run.json` | List of queries run and paths |
| `search/embeddings_cache.pkl` | Cached vector embeddings (reused on next run) |

**Options:**
- `--data-path PATH` — Use a custom path to `skills_raw.jsonl`
- `--no-queries` — Only build indices and save metadata; do not run example queries

## Usage

### Command-Line Interface

**Basic usage:**
```bash
python cli.py "your search query"
```

**Examples:**

```bash
# Search for React testing tools
python cli.py "react testing framework"

# Get top 5 results instead of default 3
python cli.py "deployment kubernetes" --top-k 5

# Show detailed scoring breakdown
python cli.py "python django" --verbose

# Output only skill names (useful for scripting)
python cli.py "browser automation" --names-only
```

**CLI Options:**
- `query` - Search query (required)
- `--top-k N` - Number of results to return (default: 3)
- `--verbose, -v` - Show detailed score breakdowns
- `--names-only` - Output only skill names, one per line
- `--data-path PATH` - Custom path to skills_raw.jsonl

### Python API

```python
from search_engine import SkillSearchEngine

# Initialize engine (only once)
engine = SkillSearchEngine()

# Simple search - returns top 3 skill names
names = engine.search_names_only("react testing")
print(names)  # ['vitest', 'react-testing-library', 'jest']

# Detailed search - returns full skill data with scores
results = engine.search("react testing", top_k=3, verbose=True)

for result in results:
    print(f"Name: {result['name']}")
    print(f"Score: {result['final_score']:.4f}")
    print(f"Description: {result['description']}")
    print(f"Weekly installs: {result['weekly_installs']}")
    print(f"URL: {result['skill_url']}")
    print(f"Score breakdown: {result['score_breakdown']}")
```

## Example Output

```bash
$ python cli.py "react performance optimization"

================================================================================
TOP 3 RECOMMENDATIONS
================================================================================

1. vercel-react-best-practices
   ──────────────────────────────────────────────────────────────────────
   React and Next.js performance optimization guidelines from Vercel
   Engineering. This skill should be used when writing, reviewing, or...

   📊 Weekly installs: 223.0K
   📈 Total installs: 222973
   📅 First seen: Jan 26, 2026
   🔗 URL: https://github.com/vercel-labs/agent-skills

   ⭐ Relevance Score: 0.8542

2. react-patterns
   ──────────────────────────────────────────────────────────────────────
   React component patterns, hooks best practices, and performance...

   📊 Weekly installs: 45.2K
   📈 Total installs: 89034
   📅 First seen: Jan 15, 2026
   🔗 URL: https://github.com/example/react-patterns

   ⭐ Relevance Score: 0.7891

3. nextjs-optimization
   ──────────────────────────────────────────────────────────────────────
   Next.js specific optimization techniques including image optimization...

   📊 Weekly installs: 32.1K
   📈 Total installs: 67234
   📅 First seen: Jan 20, 2026
   🔗 URL: https://github.com/example/nextjs-optimization

   ⭐ Relevance Score: 0.7423

================================================================================
```

## File Structure

```
search/
├── __init__.py              # Package initialization
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── data_loader.py          # Load and parse JSONL data
├── bm25_retriever.py       # BM25 keyword search
├── vector_retriever.py     # Semantic vector search
├── reranker.py             # Custom scoring and reranking
├── search_engine.py        # Main orchestrator
├── cli.py                  # Command-line interface
└── embeddings_cache.pkl    # Cached embeddings (generated)
```

## How It Works

### 1. Data Loading (`data_loader.py`)
- Parses `skills_raw.jsonl` (981 skills)
- Normalizes text fields (removes HTML entities)
- Parses install counts ("223.0K" → 223000)
- Parses dates ("Jan 26, 2026" → datetime)
- Creates searchable text: `name + description + example_usage`

### 2. BM25 Retrieval (`bm25_retriever.py`)
- Tokenizes documents (lowercase, no stopwords)
- Builds inverted index with BM25Okapi
- Returns top 25 results with BM25 scores
- Fast keyword matching

### 3. Vector Retrieval (`vector_retriever.py`)
- Uses `all-MiniLM-L6-v2` model (fast & accurate)
- Embeds: `name + description` for each skill
- Caches embeddings to `embeddings_cache.pkl`
- Computes cosine similarity for semantic matching
- Returns top 25 results

### 4. Merge & Deduplicate
- Combines BM25 and vector results
- Keeps higher score for duplicates
- Typically 30-40 unique candidates

### 5. Two-Stage Reranking (`reranker.py`)

**Stage 1: Relevance-First Ranking**
- Computes base score from:
  1. **Retrieval score** (50%): Normalized BM25/vector score
  2. **Title match** (10%): Exact (1.0) / partial (0.5) / word overlap (0.3)
- Ranks all candidates and takes top N (default: 50)

**Stage 2: Conditional Popularity Boost**
- For top N candidates, checks relevance threshold (default: 0.4)
- **If retrieval_score ≥ threshold**: Adds popularity signals:
  - **Recency** (15%): `1 / (1 + days_old / 30)` - exponential decay
  - **Weekly installs** (15%): Log-normalized current popularity
  - **Total installs** (10%): Log-normalized overall adoption
- **If retrieval_score < threshold**: Uses only stage 1 score (no popularity boost)
- Returns top 3 final results

This prevents popular but irrelevant skills from ranking high.

## Performance

- **Initial setup**: 2-3 minutes (model download + embedding generation)
- **Subsequent searches**: < 1 second
- **Memory usage**: ~500MB (model + embeddings)
- **Dataset size**: 981 skills, ~8.5MB JSONL

## Testing

Each module includes a `__main__` block for testing:

```bash
# Test data loader
python data_loader.py

# Test BM25 retriever
python bm25_retriever.py

# Test vector retriever
python vector_retriever.py

# Test reranker
python reranker.py

# Test full search engine
python search_engine.py
```

## Customization

### Adjust Scoring Weights and Threshold

Edit `search_engine.py` to change reranker weights:

```python
self.reranker = Reranker(
    self.skills,
    retrieval_weight=0.5,           # Stage 1: retrieval relevance
    title_match_weight=0.1,         # Stage 1: title match bonus
    recency_weight=0.15,            # Stage 2: recency boost
    weekly_installs_weight=0.15,    # Stage 2: weekly popularity
    total_installs_weight=0.1,      # Stage 2: total popularity
    relevance_threshold=0.4         # Minimum retrieval score for stage 2 boost
)
```

### Use Different Embedding Model

Edit `vector_retriever.py`:

```python
retriever = VectorRetriever(
    skills,
    model_name='all-mpnet-base-v2'  # More accurate but slower
)
```

Available models:
- `all-MiniLM-L6-v2` (default) - Fast, 384-dim, 80MB
- `all-mpnet-base-v2` - More accurate, 768-dim, 420MB
- `multi-qa-MiniLM-L6-cos-v1` - Optimized for Q&A

### Change Result Count

```python
# Get top 25 from each retriever instead of 25
results = engine.search(query, bm25_top_k=50, vector_top_k=50)
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'rank_bm25'"
**Solution:** Install dependencies: `pip install -r requirements.txt`

### Issue: Slow first run
**Expected:** First run downloads the sentence-transformer model (~80MB) and generates embeddings. Subsequent runs are fast.

### Issue: "FileNotFoundError: Skills file not found"
**Solution:** Run from the project root or provide `--data-path`:
```bash
python cli.py "query" --data-path ../skills_scraper/data/skills_raw.jsonl
```

### Issue: Out of memory
**Solution:** Use a smaller embedding model or reduce batch size in `vector_retriever.py`

## Future Enhancements

- [ ] Add caching layer for frequent queries
- [ ] Support for filtering by date range or install threshold
- [ ] Multi-language support
- [ ] REST API endpoint
- [ ] Web UI interface
- [ ] A/B testing framework for scoring weights

## License

This project is part of the final project for INFO376.

## References

- **BM25**: Robertson & Zaragoza (2009) - "The Probabilistic Relevance Framework: BM25 and Beyond" [https://www.researchgate.net/publication/220613776_The_Probabilistic_Relevance_Framework_BM25_and_Beyond]
- **Sentence-BERT**: Reimers & Gurevych (2019) - “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks” [https://arxiv.org/abs/1908.10084]
- **Hybrid Search**: Best practices from Weaviate architecture [https://docs.weaviate.io/weaviate/concepts/search/hybrid-search]
