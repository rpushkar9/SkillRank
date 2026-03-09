#!/usr/bin/env python3
"""
SkillRank Evaluation Harness
Usage: python test_cases/eval_harness.py [--base-url http://localhost:8000] [--top-k 3] [--gt PATH]

Metrics computed per query:
  P@1, P@3, P@5  — binary precision at cutoff k
  MRR            — mean reciprocal rank of first relevant result
  NDCG@3         — position-weighted quality with graded relevance
  Latency p50/p95 — from API `took_ms` field (5 runs, first discarded)

Exit code 1 if mean P@3 < 0.15 (regression gate).
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Ground-truth loading
# ---------------------------------------------------------------------------

def load_ground_truth(path: str | Path) -> list[dict]:
    with open(path) as f:
        items = json.load(f)
    if not items:
        raise ValueError("Ground truth is empty")
    return items


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def call_search(
    base_url: str,
    query: str,
    k: int,
    n_runs: int = 5,
) -> tuple[list[str], list[float]]:
    """Return (result_skill_ids, latency_samples_ms).

    Sends n_runs requests, discards the first (cold-start), returns all latencies.
    skill_ids come from the *last* run (results are deterministic for vector search).
    """
    params = urllib.parse.urlencode({"q": query, "k": k})
    url = f"{base_url.rstrip('/')}/api/v1/search?{params}"

    latencies: list[float] = []
    skill_ids: list[str] = []

    for i in range(n_runs):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Cannot reach backend at {base_url}: {exc}\n"
                "Make sure the backend is running before running eval."
            ) from exc

        latencies.append(float(data.get("took_ms", 0.0)))
        skill_ids = [r["skill_id"] for r in data.get("results", [])]

    # Discard first run (cold-start), keep rest
    return skill_ids, latencies[1:]


# ---------------------------------------------------------------------------
# Metric implementations
# ---------------------------------------------------------------------------

def precision_at_k(results: list[str], relevant_ids: list[str], k: int) -> float:
    if not relevant_ids or k == 0:
        return 0.0
    hits = sum(1 for r in results[:k] if r in relevant_ids)
    return hits / k


def mrr(results: list[str], relevant_ids: list[str]) -> float:
    if not relevant_ids:
        return 0.0
    for rank, skill_id in enumerate(results, start=1):
        if skill_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(results: list[str], graded: dict[str, int], k: int) -> float:
    """Normalised Discounted Cumulative Gain at cutoff k.

    DCG = sum_{i=1}^{k} grade_i / log2(i+1)
    IDCG = DCG of ideal ranking (top grades sorted descending)
    NDCG = DCG / IDCG  (0 if IDCG == 0)
    """
    if not graded or k == 0:
        return 0.0

    def dcg(ranking: list[int]) -> float:
        return sum(g / math.log2(i + 2) for i, g in enumerate(ranking[:k]))

    actual_grades = [graded.get(skill_id, 0) for skill_id in results[:k]]
    ideal_grades = sorted(graded.values(), reverse=True)

    idcg = dcg(ideal_grades)
    if idcg == 0.0:
        return 0.0
    return dcg(actual_grades) / idcg


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _pct(v: float) -> str:
    return f"{v:.2f}"


def print_markdown_table(rows: list[dict]) -> None:
    cols = [
        ("QID",      "query_id",  6),
        ("Query",    "query_short", 44),
        ("P@1",      "p1",        5),
        ("P@3",      "p3",        5),
        ("MRR",      "mrr",       5),
        ("NDCG@3",   "ndcg",      7),
        ("p50ms",    "p50",       7),
        ("p95ms",    "p95",       7),
    ]

    header = " | ".join(f"{label:<{w}}" for label, _, w in cols)
    sep    = " | ".join("-" * w for _, _, w in cols)
    print(f"\n| {header} |")
    print(f"| {sep} |")

    for row in rows:
        row["query_short"] = (row["query"] + " " * 44)[:44]
        cells = []
        for label, key, w in cols:
            val = row[key]
            if isinstance(val, float):
                cells.append(f"{val:<{w}.2f}")
            else:
                cells.append(f"{str(val):<{w}}")
        print(f"| {' | '.join(cells)} |")

    # Summary row
    print()
    metrics = ["p1", "p3", "mrr", "ndcg", "p50", "p95"]
    means = {m: statistics.mean(r[m] for r in rows) for m in metrics}
    print(f"Mean  P@1={means['p1']:.3f}  P@3={means['p3']:.3f}  "
          f"MRR={means['mrr']:.3f}  NDCG@3={means['ndcg']:.3f}  "
          f"Latency p50={means['p50']:.1f}ms  p95={means['p95']:.1f}ms")
    print()


def write_json_results(rows: list[dict], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"eval_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"Results written to {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Main eval loop
# ---------------------------------------------------------------------------

def run_eval(base_url: str, top_k: int, gt_path: Path) -> list[dict]:
    items = load_ground_truth(gt_path)
    rows: list[dict] = []

    print(f"Evaluating {len(items)} queries against {base_url} (top_k={top_k}) …\n")

    for item in items:
        qid   = item["query_id"]
        query = item["query"]
        rel   = item["relevant_ids"]
        graded = item.get("graded", {})
        in_ds  = item.get("in_dataset", True)

        print(f"  [{qid}] {query[:60]}", end="", flush=True)

        try:
            result_ids, latencies = call_search(base_url, query, top_k)
        except RuntimeError as exc:
            print(f"\nERROR: {exc}")
            sys.exit(1)

        p1   = precision_at_k(result_ids, rel, 1)
        p3   = precision_at_k(result_ids, rel, 3)
        p5   = precision_at_k(result_ids, rel, 5)
        m    = mrr(result_ids, rel)
        nd   = ndcg_at_k(result_ids, graded, 3)
        p50  = statistics.median(latencies) if latencies else 0.0
        p95  = (sorted(latencies)[int(len(latencies) * 0.95)] if latencies
                else 0.0)

        print(f"  P@3={p3:.2f}  MRR={m:.2f}  NDCG={nd:.2f}  "
              f"p50={p50:.0f}ms" + (" [unanswerable]" if not in_ds else ""))

        rows.append({
            "query_id":   qid,
            "query":      query,
            "query_short": query,
            "category":   item.get("category", ""),
            "in_dataset": in_ds,
            "p1":         round(p1, 4),
            "p3":         round(p3, 4),
            "p5":         round(p5, 4),
            "mrr":        round(m, 4),
            "ndcg":       round(nd, 4),
            "p50":        round(p50, 2),
            "p95":        round(p95, 2),
            "returned":   result_ids,
            "expected":   rel,
            "graded":     graded,
            "latencies":  [round(l, 2) for l in latencies],
        })

    return rows


# ---------------------------------------------------------------------------
# Argument parsing + entrypoint
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    here = Path(__file__).parent
    parser = argparse.ArgumentParser(description="SkillRank evaluation harness")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results to retrieve per query (default: 3)",
    )
    parser.add_argument(
        "--gt",
        default=str(here / "ground_truth.json"),
        help="Path to ground truth JSON (default: test_cases/ground_truth.json)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(here / "results"),
        help="Output directory for JSON results (default: test_cases/results/)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    rows = run_eval(
        base_url=args.base_url,
        top_k=args.top_k,
        gt_path=Path(args.gt),
    )

    print_markdown_table(rows)
    write_json_results(rows, Path(args.out_dir))

    mean_p3 = statistics.mean(r["p3"] for r in rows)
    REGRESSION_GATE = 0.15
    if mean_p3 < REGRESSION_GATE:
        print(
            f"REGRESSION: mean P@3 = {mean_p3:.3f} < threshold {REGRESSION_GATE}. "
            "Search quality has degraded."
        )
        sys.exit(1)
    else:
        print(f"OK: mean P@3 = {mean_p3:.3f} >= threshold {REGRESSION_GATE}.")
        sys.exit(0)
