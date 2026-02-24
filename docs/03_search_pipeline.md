# Search Pipeline (BM25 + Vector + Rerank)

Step-by-step description of the hybrid search pipeline.

---

## 1. Data loading + searchable text

- **File:** `search/data_loader.py`
- **Entry:** `load_skills(jsonl_path)` loads the JSONL and returns a list of normalized skill dicts.
- **Cleaning:** `clean_text()` strips HTML entities and normalizes whitespace for `description` and `example_usage`.
- **Searchable text (used for BM25):** Built in `load_skills()` as  
  `searchable_text = f"{name} {description} {example_usage}"`  
  So BM25 indexes **name + description + example_usage**.

---

## 2. BM25 indexing / tokenization

- **File:** `search/bm25_retriever.py`
- **Indexed text:** Each skill’s `searchable_text` (name + description + example_usage).
- **Tokenization:** `tokenize()` — two passes:
  1. Lowercase, extract alphanumeric tokens via `\b[a-z0-9]+\b`, remove English stopwords and tokens of length ≤ 1.
  2. Append **concatenated bigrams** for every adjacent token pair (e.g. `["front","end"] → "frontend"`). This makes `"frontend"`, `"front-end"`, and `"front end"` all produce the same `"frontend"` token and match each other.
- **Index:** `BM25Okapi(self.tokenized_corpus)` built in `BM25Retriever.__init__`.

---

## 3. Vector embedding text + model

- **File:** `search/vector_retriever.py`
- **Embedded text:** **Name + description only** (no `example_usage`). Built in `_get_embedding_texts()` as  
  `text = f"{skill['name']}. {skill['description']}"`
- **Model:** `all-MiniLM-L6-v2` (sentence-transformers) by default. Embeddings are created in `_load_or_create_embeddings()` and cached (e.g. `search/embeddings_cache.pkl`).

---

## 4. Retrieval top-K behavior

- **Orchestration:** `search/search_engine.py`, `SkillSearchEngine.search()`.
- **BM25:** `bm25_retriever.search(query, top_k=bm25_top_k)` — default **bm25_top_k = 25**.
- **Vector:** `vector_retriever.search(query, top_k=vector_top_k)` — default **vector_top_k = 25**.
- Each retriever returns a list of `(skill_name, score)` tuples, sorted by score descending, truncated to top K.

---

## 5. Merge logic

- **File:** `search/search_engine.py`, `_merge_results(bm25_results, vector_results)`.
- **Behavior:** Union of both result sets. Each candidate is a dict `{"name", "bm25_score", "vector_score"}`. If a skill appears in only one retriever, the other score field is `None`. The raw scores are **not combined here**; normalization and combination happen inside the reranker.
- **Output:** `List[Dict]` with one entry per unique skill name (order from dict insertion; final sort happens in the reranker).

---

## 6. Reranker scoring (stage 1 and stage 2)

- **File:** `search/reranker.py`, `Reranker.rerank(query, candidates)`.
- **Input:** `candidates` = merged list of `{"name", "bm25_score", "vector_score"}` dicts (scores may be `None`).

**Normalization**

- BM25 and vector scores are min–max normalized **independently** to [0, 1] via `_normalize_scores()` (treating `None` as 0).
- **Combined retrieval score:**
  `combined_retrieval = W_BM25 * bm25_norm + W_VEC * vector_norm`
  Defaults: **W_BM25 = 0.5**, **W_VEC = 0.5** (defined at top of `reranker.py`).

**Stage 1 — Relevance**

- For each candidate:
  - `combined_retrieval` = weighted sum of independently-normalized BM25 + vector scores (see above).
  - `title_match_score` = `_compute_title_match_score(query, skill_name)` (exact 1.0, substring 0.5, word overlap 0.3 × ratio, else 0).
- **Stage 1 score:**
  `stage1_score = combined_retrieval * retrieval_weight + title_match_score * title_match_weight`
  Defaults: **retrieval_weight = 0.5**, **title_match_weight = 0.1**.

Results are sorted by `stage1_score` and the top **top_n_for_stage2** (default **50**) are kept for stage 2.

**Stage 2 — Popularity boost (conditional)**

- For each of those top-N candidates:
  - Recency score: `1 / (1 + days_old/30)` from `first_seen`.
  - Weekly and total installs: log-scale normalized to [0, 1] via `_compute_installs_score` using precomputed log min/max/range.
- **Threshold:** If **combined_retrieval >= relevance_threshold** (default **0.4**):
  - **final_score** = stage1_score + recency × **0.15** + weekly_installs × **0.15** + total_installs × **0.1**.
- Else: **final_score** = stage1_score (no popularity boost).

Final output is sorted by `final_score` descending and returned as `(skill_name, final_score, score_breakdown)`.

---

## Summary of key implementation facts

| Item | Value |
|------|--------|
| BM25 indexed text | name + description + example_usage |
| BM25 tokenization | unigrams + adjacent concatenated bigrams |
| Vector embedded text | name + description only |
| Vector model | all-MiniLM-L6-v2 (default) |
| bm25_top_k | 25 |
| vector_top_k | 25 |
| stage2 top_n_for_stage2 | 50 |
| Merge format | `{"name", "bm25_score", "vector_score"}` dict; no score combination at merge |
| Retrieval score | BM25 and vector normalized independently; combined as W_BM25=0.5 × bm25_norm + W_VEC=0.5 × vector_norm |
| Stage 1 | retrieval_weight=0.5, title_match_weight=0.1 |
| Stage 2 threshold | combined_retrieval >= 0.4 |
| Stage 2 weights | recency 0.15, weekly_installs 0.15, total_installs 0.1 |
