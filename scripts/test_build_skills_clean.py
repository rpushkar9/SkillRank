"""
Tests for scripts/build_skills_clean.py.

Run from repo root:
    python -m pytest scripts/test_build_skills_clean.py -v
"""

import json
import sys
from pathlib import Path

# Allow imports from this directory regardless of where pytest is invoked
sys.path.insert(0, str(Path(__file__).parent))

from build_skills_clean import (
    parse_installs,
    parse_first_seen,
    clean_text,
    make_skill_id,
    make_name_norm,
    build_clean_row,
)


# ---------------------------------------------------------------------------
# parse_installs
# ---------------------------------------------------------------------------

class TestParseInstalls:
    def test_k_suffix(self):
        assert parse_installs("4.2K") == 4200

    def test_k_suffix_large(self):
        assert parse_installs("223.0K") == 223000

    def test_m_suffix(self):
        assert parse_installs("1.5M") == 1_500_000

    def test_plain_integer_string(self):
        assert parse_installs("540") == 540

    def test_zero_string(self):
        assert parse_installs("0") == 0

    def test_empty_string(self):
        assert parse_installs("") == 0

    def test_none(self):
        assert parse_installs(None) == 0

    def test_integer_value(self):
        # raw field might come in as int already
        assert parse_installs(540) == 540

    def test_with_comma(self):
        # defensive: shouldn't appear in dataset but should not crash
        assert parse_installs("1,234") == 1234

    def test_lowercase_k(self):
        assert parse_installs("4.2k") == 4200


# ---------------------------------------------------------------------------
# parse_first_seen
# ---------------------------------------------------------------------------

class TestParseFirstSeen:
    def test_standard_format(self):
        assert parse_first_seen("Jan 26, 2026") == "2026-01-26"

    def test_single_digit_day(self):
        assert parse_first_seen("Feb 3, 2026") == "2026-02-03"

    def test_empty_string(self):
        assert parse_first_seen("") == ""

    def test_none(self):
        assert parse_first_seen(None) == ""

    def test_unparseable(self):
        assert parse_first_seen("not-a-date") == ""

    def test_december(self):
        assert parse_first_seen("Dec 31, 2025") == "2025-12-31"

    def test_today(self):
        from datetime import datetime
        fake_today = datetime(2026, 2, 25)
        assert parse_first_seen("Today", _today=fake_today) == "2026-02-25"

    def test_one_day_ago(self):
        from datetime import datetime
        fake_today = datetime(2026, 2, 25)
        assert parse_first_seen("1 day ago", _today=fake_today) == "2026-02-24"

    def test_n_days_ago(self):
        from datetime import datetime
        fake_today = datetime(2026, 2, 25)
        assert parse_first_seen("12 days ago", _today=fake_today) == "2026-02-13"

    def test_case_insensitive_today(self):
        from datetime import datetime
        fake_today = datetime(2026, 2, 25)
        assert parse_first_seen("today", _today=fake_today) == "2026-02-25"


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------

class TestCleanText:
    def test_hex_html_entity(self):
        result = clean_text("npx skills add &#x3C;package>")
        assert "&#x" not in result
        assert "package" in result

    def test_named_html_entity(self):
        result = clean_text("a &amp; b")
        assert "&amp;" not in result
        assert "a" in result and "b" in result

    def test_collapses_whitespace(self):
        assert clean_text("hello   world") == "hello world"

    def test_empty(self):
        assert clean_text("") == ""

    def test_none(self):
        assert clean_text(None) == ""


# ---------------------------------------------------------------------------
# make_name_norm
# ---------------------------------------------------------------------------

class TestMakeNameNorm:
    def test_hyphen_removed(self):
        assert make_name_norm("front-end") == "frontend"

    def test_space_removed(self):
        assert make_name_norm("front end") == "frontend"

    def test_lowercased(self):
        assert make_name_norm("Frontend") == "frontend"

    def test_solid_unchanged(self):
        assert make_name_norm("nodejs") == "nodejs"


# ---------------------------------------------------------------------------
# build_clean_row — integration (tiny inline records)
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    {
        "name": "vitest",
        "description": "Vitest is a next-gen testing framework.",
        "example_usage": "Run npx vitest.",
        "weekly_installs": "4.2K",
        "total_installs": "4193",
        "first_seen": "Jan 28, 2026",
        "skill_url": "https://github.com/antfu/skills",
    },
    {
        "name": "find-skills",
        "description": "Find Skills helps you discover and install skills. &amp; more.",
        "example_usage": "Use &#x3C;package> syntax.",
        "weekly_installs": "223.0K",
        "total_installs": "222973",
        "first_seen": "Jan 26, 2026",
        "skill_url": "https://github.com/vercel-labs/skills",
    },
    {
        "name": "vue-jsx-best-practices",
        "description": "Vue JSX guidelines.",
        "example_usage": "",
        "weekly_installs": "58",
        "total_installs": "1",
        "first_seen": "",           # real edge case in dataset
        "skill_url": "https://github.com/vuejs-ai/skills",
    },
]


class TestBuildCleanRow:
    def test_basic_fields_present(self):
        row, warnings = build_clean_row(SAMPLE_ROWS[0])
        required = {
            'skill_id', 'name', 'description', 'example_usage',
            'weekly_installs_raw', 'total_installs_raw',
            'weekly_installs', 'total_installs',
            'first_seen_raw', 'first_seen_date',
            'skill_url', 'searchable_text', 'name_norm',
        }
        assert required == set(row.keys())

    def test_installs_parsed_correctly(self):
        row, _ = build_clean_row(SAMPLE_ROWS[0])
        assert row['weekly_installs'] == 4200
        assert row['total_installs'] == 4193

    def test_large_installs(self):
        row, _ = build_clean_row(SAMPLE_ROWS[1])
        assert row['weekly_installs'] == 223000
        assert row['total_installs'] == 222973

    def test_date_parsed(self):
        row, _ = build_clean_row(SAMPLE_ROWS[0])
        assert row['first_seen_date'] == "2026-01-28"

    def test_empty_date_becomes_empty_string(self):
        row, warnings = build_clean_row(SAMPLE_ROWS[2])
        assert row['first_seen_date'] == ""
        assert not warnings  # empty first_seen is not a failure — just unknown

    def test_html_entities_cleaned_in_description(self):
        row, _ = build_clean_row(SAMPLE_ROWS[1])
        assert "&amp;" not in row['description']
        assert "&#x" not in row['example_usage']

    def test_searchable_text_contains_name(self):
        row, _ = build_clean_row(SAMPLE_ROWS[0])
        assert "vitest" in row['searchable_text']

    def test_skill_id_is_40_char_hex(self):
        row, _ = build_clean_row(SAMPLE_ROWS[0])
        assert len(row['skill_id']) == 40
        assert all(c in '0123456789abcdef' for c in row['skill_id'])

    def test_skill_id_stable(self):
        """Same input always produces the same ID."""
        row1, _ = build_clean_row(SAMPLE_ROWS[0])
        row2, _ = build_clean_row(SAMPLE_ROWS[0])
        assert row1['skill_id'] == row2['skill_id']

    def test_skill_ids_differ_across_rows(self):
        id0 = build_clean_row(SAMPLE_ROWS[0])[0]['skill_id']
        id1 = build_clean_row(SAMPLE_ROWS[1])[0]['skill_id']
        id2 = build_clean_row(SAMPLE_ROWS[2])[0]['skill_id']
        assert len({id0, id1, id2}) == 3

    def test_name_norm(self):
        row, _ = build_clean_row(SAMPLE_ROWS[0])
        assert row['name_norm'] == "vitest"

    def test_no_warnings_for_clean_row(self):
        _, warnings = build_clean_row(SAMPLE_ROWS[0])
        assert warnings == []
