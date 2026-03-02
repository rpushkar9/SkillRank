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

---

---

## 2026-02-25 — skills_clean.jsonl builder

**Branch:** `feat/skills-clean-jsonl`

### What changed

**`scripts/build_skills_clean.py` — new script**

Reads `skills_raw.jsonl`, cleans every row, and writes `skills_scraper/data/skills_clean.jsonl`.

New/normalised fields per row:

| Field | Notes |
|-------|-------|
| `skill_id` | sha1(name + `\|` + skill_url) — stable unique ID |
| `weekly_installs` / `total_installs` | parsed to `int` (K/M suffixes handled) |
| `first_seen_date` | ISO `YYYY-MM-DD`; relative strings (`"12 days ago"`, `"Today"`) resolved at run time |
| `searchable_text` | HTML entities removed (`&#x3C;`, `&amp;`, etc.) |
| `name_norm` | lowercase, hyphens/spaces removed — for loose matching |

Run: `python scripts/build_skills_clean.py`

**`scripts/test_build_skills_clean.py` — 41 unit tests**

Covers `parse_installs`, `parse_first_seen` (including relative-date formats), `clean_text`, `make_name_norm`, and `build_clean_row` (schema, stability, dedup).

Run: `python -m pytest scripts/test_build_skills_clean.py -v`

**`search/data_loader.py` — minimal dual-schema support**

- `parse_date()` now also accepts ISO `YYYY-MM-DD` strings (in addition to `"Jan 26, 2026"`).
- `load_skills()` falls back to `first_seen_date` key when `first_seen` key is absent (clean JSONL).
- No behaviour change when loading the raw JSONL.

**Docs updated:** `docs/02_data_stats.md`, `docs/00_repo_map.md`

### Parse edge cases found

- 125 rows in raw JSONL have relative `first_seen` strings (`"N days ago"`, `"Today"`) — now resolved.
- 1 row has a blank `first_seen` (`vue-jsx-best-practices`) → `first_seen_date: ""`.
- `total_installs` is always a plain integer string; no K/M suffix needed.
- HTML entities (`&#x3C;`, `&#x26;`, `&amp;`) appear frequently in `example_usage`.
- 0 duplicate `skill_id` values — all 981 rows have unique (name, skill_url) pairs.
- 34 duplicate names across different repos (e.g. `frontend-design` × 4, `skill-creator` × 6).

---

## 2026-02-25 — Session checkpoint

- Verified end-to-end CLI run on `skills_clean.jsonl`: ISO dates now render correctly (`2026-01-17`) in `--verbose` output; all 57 tests pass.
- Created session log `docs/sessions/2026-02-25.md` with full context, git snapshot, run commands, CLI evidence, and warning explanations.
- Updated `docs/03_search_pipeline.md` (new §0 Cleaned dataset, new §7 `--trace`), `docs/02_data_stats.md` (cleaned-dataset stats table), `docs/00_repo_map.md` (venv note, data files section).

---

## 2026-02-23 — Session checkpoint

Full session log (context, decisions, open items, resume instructions):
→ `docs/sessions/2026-02-23.md`

