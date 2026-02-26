#!/usr/bin/env python3
"""
Build skills_clean.jsonl from skills_raw.jsonl.

Usage (from repo root, venv active):
    python scripts/build_skills_clean.py
    python scripts/build_skills_clean.py --input skills_scraper/data/skills_raw.jsonl \\
                                          --output skills_scraper/data/skills_clean.jsonl
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Pure parsing helpers (imported by tests)
# ---------------------------------------------------------------------------

def parse_installs(value) -> int:
    """
    Parse install-count strings like '223.0K', '4.2K', '540', '' to int.

    Handles:
      '223.0K' -> 223000
      '4.2K'   -> 4200
      '1.5M'   -> 1500000
      '540'    -> 540
      ''/ None -> 0
    """
    if value is None:
        return 0
    s = str(value).strip().upper()
    if not s:
        return 0
    try:
        if s.endswith('K'):
            return int(float(s[:-1]) * 1_000)
        if s.endswith('M'):
            return int(float(s[:-1]) * 1_000_000)
        # Plain integer or decimal; strip commas just in case
        return int(float(s.replace(',', '')))
    except (ValueError, TypeError):
        return 0


def parse_first_seen(value, _today: datetime = None) -> str:
    """
    Parse first_seen strings to ISO date 'YYYY-MM-DD', or '' on failure.

    Handles:
      'Jan 26, 2026'  -> '2026-01-26'   (absolute date from scraper)
      'Today'         -> today's date   (relative — scraper ran today)
      '1 day ago'     -> yesterday
      'N days ago'    -> today - N days
      ''/ None        -> ''
    """
    if not value:
        return ''
    s = str(value).strip()
    if not s:
        return ''

    today = _today or datetime.now()

    # Absolute date: "Jan 26, 2026"
    try:
        dt = datetime.strptime(s, "%b %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Relative: "Today"
    if s.lower() == 'today':
        return today.strftime("%Y-%m-%d")

    # Relative: "1 day ago" or "N days ago"
    m = re.match(r'^(\d+)\s+days?\s+ago$', s, re.IGNORECASE)
    if m:
        from datetime import timedelta
        delta = int(m.group(1))
        dt = today - timedelta(days=delta)
        return dt.strftime("%Y-%m-%d")

    return ''


def clean_text(text: str) -> str:
    """Remove HTML entities and collapse whitespace."""
    if not text:
        return ''
    # Hex entities: &#x3C; &#x26; etc.
    text = re.sub(r'&#x[0-9A-Fa-f]+;', ' ', text)
    # Named entities: &amp; &lt; &gt; etc.
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def make_skill_id(name: str, skill_url: str) -> str:
    """Stable unique ID: sha1(name + '|' + skill_url) hex digest."""
    key = f"{name}|{skill_url}".encode('utf-8')
    return hashlib.sha1(key).hexdigest()


def make_name_norm(name: str) -> str:
    """Lowercase, hyphens and spaces removed: 'front-end' -> 'frontend'."""
    return re.sub(r'[-\s]', '', name.lower())


# ---------------------------------------------------------------------------
# Row builder
# ---------------------------------------------------------------------------

def build_clean_row(raw: dict) -> Tuple[dict, List[str]]:
    """
    Convert a raw JSONL row to the clean schema.

    Returns:
        (clean_row_dict, warnings)
        warnings is a list of human-readable strings for any parse failures.
    """
    warnings: List[str] = []

    name = str(raw.get('name', '')).strip()
    description = clean_text(raw.get('description', ''))
    example_usage = clean_text(raw.get('example_usage', ''))
    skill_url_val = str(raw.get('skill_url', '')).strip()

    # Installs
    weekly_raw = str(raw.get('weekly_installs', ''))
    total_raw = str(raw.get('total_installs', ''))
    weekly_int = parse_installs(weekly_raw)
    total_int = parse_installs(total_raw)

    if weekly_raw and weekly_int == 0 and weekly_raw not in ('0', ''):
        warnings.append(f"weekly_installs parse failure: {weekly_raw!r} (name={name!r})")
    if total_raw and total_int == 0 and total_raw not in ('0', ''):
        warnings.append(f"total_installs parse failure: {total_raw!r} (name={name!r})")

    # Date — empty raw value is allowed (one row in dataset has no date)
    first_seen_raw = str(raw.get('first_seen', '')).strip()
    first_seen_iso = parse_first_seen(first_seen_raw)
    if first_seen_raw and not first_seen_iso:
        warnings.append(f"first_seen parse failure: {first_seen_raw!r} (name={name!r})")

    # Searchable text: HTML-cleaned combination of all text fields
    searchable = f"{name} {description} {example_usage}"
    searchable = re.sub(r'\s+', ' ', searchable).strip()

    clean_row = {
        'skill_id': make_skill_id(name, skill_url_val),
        'name': name,
        'description': description,
        'example_usage': example_usage,
        'weekly_installs_raw': weekly_raw,
        'total_installs_raw': total_raw,
        'weekly_installs': weekly_int,
        'total_installs': total_int,
        'first_seen_raw': first_seen_raw,
        'first_seen_date': first_seen_iso,
        'skill_url': skill_url_val,
        'searchable_text': searchable,
        'name_norm': make_name_norm(name),
    }
    return clean_row, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Build skills_clean.jsonl from skills_raw.jsonl'
    )
    parser.add_argument(
        '--input',
        default='skills_scraper/data/skills_raw.jsonl',
        help='Path to input JSONL (default: skills_scraper/data/skills_raw.jsonl)',
    )
    parser.add_argument(
        '--output',
        default='skills_scraper/data/skills_clean.jsonl',
        help='Path to output JSONL (default: skills_scraper/data/skills_clean.jsonl)',
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Read raw rows
    raw_rows: List[dict] = []
    with open(input_path, encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                raw_rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  WARN: JSON parse error on line {line_num}: {e}", file=sys.stderr)

    # Build clean rows; deduplicate by skill_id (keep first occurrence)
    clean_rows: List[dict] = []
    all_warnings: List[str] = []
    seen_ids: Dict[str, bool] = {}

    for raw in raw_rows:
        clean_row, warnings = build_clean_row(raw)
        all_warnings.extend(warnings)
        sid = clean_row['skill_id']
        if sid in seen_ids:
            continue
        seen_ids[sid] = True
        clean_rows.append(clean_row)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for row in clean_rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')

    # ---------- Report ----------
    print(f"Input:   {input_path}  ({len(raw_rows)} rows read)")
    print(f"Output:  {output_path}  ({len(clean_rows)} rows written)")

    dup_id_count = len(raw_rows) - len(clean_rows)
    print(f"Duplicate skill_ids removed: {dup_id_count}  "
          f"({'none — all IDs unique' if dup_id_count == 0 else 'kept first occurrence'})")

    if all_warnings:
        print(f"\nParse warnings ({len(all_warnings)}):")
        for w in all_warnings[:20]:
            print(f"  {w}")
        if len(all_warnings) > 20:
            print(f"  ... and {len(all_warnings) - 20} more")
    else:
        print("\nNo parse failures.")

    # Duplicate names (name-only, not name+url)
    name_counter = Counter(r['name'] for r in raw_rows)
    dup_names = [(n, c) for n, c in name_counter.most_common(10) if c > 1]
    if dup_names:
        print(f"\nTop duplicate names in raw input (same name, different URLs):")
        for name, count in dup_names:
            print(f"  {count}x  {name}")
    else:
        print("\nNo duplicate names found.")

    # Date parsing coverage
    missing_date = sum(1 for r in clean_rows if not r['first_seen_date'])
    print(f"\nRows with empty first_seen_date: {missing_date}")

    print("\nDone.")


if __name__ == '__main__':
    main()
