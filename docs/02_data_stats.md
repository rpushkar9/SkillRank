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
