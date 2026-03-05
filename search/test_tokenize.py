"""
Unit tests for bm25_retriever.tokenize().

Run from the search/ directory:
    python -m pytest test_tokenize.py -v
"""

import sys
from pathlib import Path

# Allow running from repo root too
sys.path.insert(0, str(Path(__file__).parent))

from bm25_retriever import tokenize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def has_compound(tokens, compound):
    """Return True if *compound* appears in *tokens*."""
    return compound in tokens


# ---------------------------------------------------------------------------
# frontend / front-end / front end
# ---------------------------------------------------------------------------

class TestFrontend:
    def test_solid_word_contains_frontend(self):
        tokens = tokenize("frontend")
        assert "frontend" in tokens

    def test_hyphenated_contains_frontend(self):
        # "front-end" splits into ["front", "end"]; bigram → "frontend"
        tokens = tokenize("front-end")
        assert has_compound(tokens, "frontend"), f"tokens={tokens}"

    def test_spaced_contains_frontend(self):
        # "front end" splits into ["front", "end"]; bigram → "frontend"
        tokens = tokenize("front end")
        assert has_compound(tokens, "frontend"), f"tokens={tokens}"

    def test_all_three_share_frontend_token(self):
        solid = set(tokenize("frontend"))
        hyphen = set(tokenize("front-end"))
        spaced = set(tokenize("front end"))
        assert "frontend" in solid & hyphen & spaced

    def test_unigrams_preserved(self):
        tokens = tokenize("front end")
        assert "front" in tokens
        assert "end" in tokens


# ---------------------------------------------------------------------------
# nodejs / node-js / node js
# ---------------------------------------------------------------------------

class TestNodejs:
    def test_solid_word_contains_nodejs(self):
        tokens = tokenize("nodejs")
        assert "nodejs" in tokens

    def test_hyphenated_contains_nodejs(self):
        tokens = tokenize("node-js")
        assert has_compound(tokens, "nodejs"), f"tokens={tokens}"

    def test_spaced_contains_nodejs(self):
        tokens = tokenize("node js")
        assert has_compound(tokens, "nodejs"), f"tokens={tokens}"

    def test_all_three_share_nodejs_token(self):
        solid = set(tokenize("nodejs"))
        hyphen = set(tokenize("node-js"))
        spaced = set(tokenize("node js"))
        assert "nodejs" in solid & hyphen & spaced


# ---------------------------------------------------------------------------
# Stable behaviour: other cases should not regress
# ---------------------------------------------------------------------------

class TestStableBehaviour:
    def test_stopwords_removed(self):
        tokens = tokenize("the quick brown fox")
        assert "the" not in tokens

    def test_single_char_removed(self):
        tokens = tokenize("a b c react")
        assert "a" not in tokens
        assert "b" not in tokens
        assert "react" in tokens

    def test_empty_string(self):
        assert tokenize("") == []

    def test_stopwords_only(self):
        assert tokenize("the and or is") == []

    def test_numbers_kept(self):
        tokens = tokenize("python3 version 10")
        assert "python3" in tokens

    def test_multi_word_query(self):
        # "react testing framework" → unigrams + bigrams
        tokens = tokenize("react testing framework")
        assert "react" in tokens
        assert "testing" in tokens
        assert "framework" in tokens
        # bigrams
        assert "reacttesting" in tokens
        assert "testingframework" in tokens


# ---------------------------------------------------------------------------
# --trace CLI flag smoke test (no ML stack required)
# ---------------------------------------------------------------------------

class TestTraceCLI:
    """Verify --trace is a recognised argument without running the engine."""

    def test_trace_flag_in_help_output(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "cli.py", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
        )
        assert result.returncode == 0
        assert "--trace" in result.stdout
