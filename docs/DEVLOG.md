# DEVLOG

---

## 2026-02-23 — BM25 token normalization + pipeline doc update

**Branch:** `feat/bm25-token-normalization`

### What changed

**`search/bm25_retriever.py` — concatenated bigrams in `tokenize()`**

After the base tokenization + stopword filtering pass, we now append a
concatenated bigram for every adjacent token pair. Example:

```
"front-end"  → ["front", "end", "frontend"]
"front end"  → ["front", "end", "frontend"]
"frontend"   → ["frontend"]
```

All three surface forms of a compound term now share the same compound
token, so BM25 no longer misses hyphenated or spaced variants of a term
that appears in skill names (e.g. `"node-js"` vs `"nodejs"`).

**`search/test_tokenize.py` — new unit test file**

15 tests covering:
- `frontend` / `front-end` / `front end` all share `"frontend"` token
- `nodejs` / `node-js` / `node js` all share `"nodejs"` token
- Stable-behaviour regression cases (stopwords, single chars, empty input, numbers, multi-word bigrams)

Run: `cd search && python -m pytest test_tokenize.py -v`

**`docs/03_search_pipeline.md` — corrected to match current code**

- §2 BM25 tokenization: documents the new bigram step.
- §5 Merge logic: corrected from the old max-merge description to the
  current dict-based format `{"name", "bm25_score", "vector_score"}` with
  no score combination at merge time.
- §6 Reranker: corrected `retrieval_score` → `combined_retrieval`,
  documents independent normalization + `W_BM25 * bm25_norm + W_VEC * vector_norm`.
- Summary table updated to match.

### Why

The old tokenizer split on non-alphanumeric characters but never
recombined adjacent tokens. Queries like `"front-end"` would produce
`["front", "end"]`, which scored poorly against skills whose text
contained `"frontend"` (a single token). The bigram fix closes this gap
without removing any existing unigram tokens, so recall is strictly
improved.

The pipeline doc was still describing the pre-`feat/separate-bm25-vector-scores`
merge behaviour (max-merge + single retrieval_score), which was incorrect.

