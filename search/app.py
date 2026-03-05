"""
Flask web app for the SkillRank search engine.

Run from the repo root or from the search/ directory:

    cd SkillRank
    python3 search/app.py

or:

    cd SkillRank/search
    python3 app.py
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request


# Ensure we can import the search package when run from repo root
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from search_engine import SkillSearchEngine  # type: ignore


app = Flask(__name__, template_folder="templates")

_engine: SkillSearchEngine | None = None


def get_engine() -> SkillSearchEngine:
    """Lazy-initialize the search engine so first request does the heavy work."""
    global _engine
    if _engine is None:
        _engine = SkillSearchEngine()
    return _engine


@app.route("/")
def index() -> Any:
    return render_template("index.html")


@app.route("/api/search")
def api_search() -> Any:
    """JSON API that wraps SkillSearchEngine.search."""
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"error": "Missing query parameter 'q'.", "results": []}), 400

    try:
        k_raw = request.args.get("k", "5")
        k = max(1, min(int(k_raw), 10))
    except ValueError:
        k = 5

    engine = get_engine()
    results = engine.search(query, top_k=k, verbose=False)

    payload: List[Dict[str, Any]] = []
    for r in results:
        payload.append(
            {
                "name": r["name"],
                "description": r["description"],
                "skill_url": r["skill_url"],
                "weekly_installs": int(r["weekly_installs"]),
                "total_installs": int(r["total_installs"]),
                "first_seen": r.get("first_seen", ""),
                "final_score": float(r["final_score"]),
            }
        )

    return jsonify({"query": query, "results": payload})


if __name__ == "__main__":
    print("Starting SkillRank UI at http://127.0.0.1:5000")
    print("First search may take a few seconds while the model loads.")
    app.run(host="127.0.0.1", port=5000, debug=True)

