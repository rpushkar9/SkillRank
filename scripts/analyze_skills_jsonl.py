#!/usr/bin/env python3
"""
Analyze skills_scraper/data/skills_raw.jsonl:
- total rows
- per-field: % missing, % empty string, example non-empty values (up to 3)
- length distribution for description and example_usage (min/median/p95/max)
"""

import json
from pathlib import Path
from collections import defaultdict

DATA_PATH = Path(__file__).resolve().parent.parent / "skills_scraper" / "data" / "skills_raw.jsonl"


def main():
    rows = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    n = len(rows)
    print("=" * 70)
    print("SKILLS_RAW.JSONL — SUMMARY")
    print("=" * 70)
    print(f"\nTotal rows: {n}\n")

    # Collect all keys and stats per key
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    all_keys = sorted(all_keys)

    # Per-field: missing, empty, examples
    missing = defaultdict(int)
    empty = defaultdict(int)
    examples = defaultdict(list)  # up to 3 non-empty examples per key

    for r in rows:
        for k in all_keys:
            val = r.get(k)
            if val is None or k not in r:
                missing[k] += 1
            elif val == "":
                empty[k] += 1
            else:
                if len(examples[k]) < 3:
                    s = str(val)
                    if len(s) > 80:
                        s = s[:77] + "..."
                    examples[k].append(s)

    print("-" * 70)
    print("PER-FIELD: % missing, % empty string, example non-empty values")
    print("-" * 70)
    print(f"{'Field':<20} {'% missing':>12} {'% empty':>12}  Examples (up to 3)")
    print("-" * 70)
    for k in all_keys:
        pct_miss = 100 * missing[k] / n
        pct_empty = 100 * empty[k] / n
        ex_str = " | ".join(examples[k]) if examples[k] else "(none)"
        print(f"{k:<20} {pct_miss:>11.1f}% {pct_empty:>11.1f}%  {ex_str}")
    print()

    # Length distribution for description and example_usage
    len_fields = ["description", "example_usage"]
    lens = {f: [] for f in len_fields}
    for r in rows:
        for f in len_fields:
            val = r.get(f)
            if val is not None and val != "":
                lens[f].append(len(str(val)))

    print("-" * 70)
    print("LENGTH DISTRIBUTION (description, example_usage)")
    print("-" * 70)
    print(f"{'Field':<20} {'min':>10} {'median':>10} {'p95':>10} {'max':>10}")
    print("-" * 70)
    for f in len_fields:
        arr = sorted(lens[f]) if lens[f] else [0]
        min_len = arr[0]
        median_len = arr[len(arr) // 2] if arr else 0
        p95_idx = int(len(arr) * 0.95) - 1
        p95_len = arr[max(0, p95_idx)] if arr else 0
        max_len = arr[-1] if arr else 0
        print(f"{f:<20} {min_len:>10} {median_len:>10} {p95_len:>10} {max_len:>10}")
    print("=" * 70)


if __name__ == "__main__":
    main()
