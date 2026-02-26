# Dataset Stats (skills_raw.jsonl)

## Total rows

- **981 rows** (one blank line in the file is skipped by the loader).
- File: `skills_scraper/data/skills_raw.jsonl` (982 lines total).

## Missingness summary

- **No missing keys:** Every row has all seven keys (`name`, `description`, `example_usage`, `weekly_installs`, `first_seen`, `skill_url`, `total_installs`).
- **Empty strings:** A small share of rows have empty strings, e.g. ~0.8% for `description` and `example_usage`; other fields have 0–0.4% empty.

## Length distribution

Character-length stats for the two long text fields:

| Field           | min | median | p95   | max   |
|-----------------|-----|--------|-------|-------|
| description     | 21  | 132    | 706   | 7,048 |
| example_usage   | 536 | 6,385  | 20,362 | 59,017 |

## How to run the analysis script

From the repo root:

```bash
python3 scripts/analyze_skills_jsonl.py
```

- **Script path:** `scripts/analyze_skills_jsonl.py`
- The script reads `skills_scraper/data/skills_raw.jsonl`, prints total rows, per-field % missing / % empty with up to 3 example non-empty values, and the length distribution table above.

---

## Cleaned dataset

**File:** `skills_scraper/data/skills_clean.jsonl`
**Rows:** 981 (same as raw; all `skill_id` values are unique — 0 duplicates removed)

### Schema changes from raw

| Field | Type | Notes |
|-------|------|-------|
| `skill_id` | string | sha1(name + `\|` + skill_url) — stable unique ID |
| `name` | string | unchanged |
| `description` | string | HTML entities removed, whitespace collapsed |
| `example_usage` | string | same cleaning |
| `weekly_installs_raw` | string | original string from scraper (e.g. `"4.2K"`) |
| `total_installs_raw` | string | original string from scraper |
| `weekly_installs` | int | parsed from raw (K/M suffixes handled) |
| `total_installs` | int | parsed from raw |
| `first_seen_raw` | string | original string from scraper |
| `first_seen_date` | string | ISO `YYYY-MM-DD`; `""` if blank (1 row) |
| `skill_url` | string | unchanged |
| `searchable_text` | string | HTML-cleaned `name + description + example_usage` |
| `name_norm` | string | lowercase, hyphens/spaces removed (e.g. `"frontend"`) |

### Parse edge cases found

- **`weekly_installs`:** always uses K suffix or plain integer — no failures.
- **`total_installs`:** always plain integer string — no failures.
- **`first_seen`:** 125 rows used relative strings (`"12 days ago"`, `"Today"`) instead of absolute dates. The cleaner resolves these relative to the run date. 1 row has a blank `first_seen` (name: `vue-jsx-best-practices`), which produces `first_seen_date: ""`.
- **HTML entities:** `&#x3C;` (`<`), `&#x26;` (`&`), `&amp;`, `&lt;` etc. appear frequently in `example_usage`. All removed by `clean_text()`.

### How to build / rebuild

```bash
python scripts/build_skills_clean.py
```

Point the search CLI at the clean file:

```bash
python search/cli.py "frontend" --data-path skills_scraper/data/skills_clean.jsonl --top-k 5 --verbose
```
