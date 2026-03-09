"""Week-4 Retrieval Optimization — query performance evaluation script.

Runs a battery of representative medical queries against both retrieval
strategies (pgvector and FAISS) and reports latency, chunk counts, score
distributions, and metadata completeness.

Usage
-----
    # Run against live Supabase (pgvector only):
    python -m backend.scripts.eval_retrieval --user-id <UUID>

    # Run against both pgvector and FAISS:
    python -m backend.scripts.eval_retrieval --user-id <UUID> --strategies pgvector faiss

    # Custom threshold sweep:
    python -m backend.scripts.eval_retrieval --user-id <UUID> --thresholds 0.3 0.4 0.5 0.6

Environment Variables
---------------------
    SUPABASE_URL        — Supabase project URL (required)
    SUPABASE_KEY        — Supabase service-role key (required)
    RETRIEVAL_TOP_K     — Default top-k (overridable via --top-k)
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from typing import Any, Dict, List

# Week-4 Retrieval Optimization — evaluation script

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("eval_retrieval")

# ── Representative medical queries ───────────────────────────────────────────
# These are the kinds of questions users and doctors typically ask the RAG
# system.  They span different report sections to exercise section-label
# filtering and diverse embedding similarity patterns.

DEFAULT_QUERIES = [
    "What is the patient's HbA1c level?",
    "Show recent cholesterol and lipid panel results",
    "Are there any abnormal blood test values?",
    "What is the patient's vitamin D level?",
    "Show kidney function test results including creatinine and urea",
    "What did the MRI scan reveal?",
    "Summarize the doctor's recommendations",
    "What are the patient's recent vital signs?",
    "How has the hemoglobin level changed over time?",
    "What sleep metrics are available for this patient?",
]

# Expected section labels for each query (for metadata quality checks)
EXPECTED_SECTIONS: Dict[str, str] = {
    "What is the patient's HbA1c level?": "blood_test",
    "Show recent cholesterol and lipid panel results": "blood_test",
    "Are there any abnormal blood test values?": "blood_test",
    "What is the patient's vitamin D level?": "blood_test",
    "Show kidney function test results including creatinine and urea": "blood_test",
    "What did the MRI scan reveal?": "imaging",
    "Summarize the doctor's recommendations": "summary",
    "What are the patient's recent vital signs?": "vitals",
    "How has the hemoglobin level changed over time?": "blood_test",
    "What sleep metrics are available for this patient?": "sleep_data",
}

# Required metadata keys that every returned chunk must contain
REQUIRED_METADATA_KEYS = {
    "source_filename",
    "source_url",
    "page_number",
    "source",
    "section_label",
    "report_date",
    "embedding_version",
}


def run_single_query(
    user_id: str,
    query: str,
    *,
    strategy: str,
    top_k: int,
    match_threshold: float,
    section_filter: str | None = None,
) -> Dict[str, Any]:
    """Execute a single retrieval call and capture metrics."""
    from backend.services.retrieval import retrieve_context

    t0 = time.perf_counter()
    result = retrieve_context(
        user_id=user_id,
        query=query,
        top_k=top_k,
        match_threshold=match_threshold,
        section_filter=section_filter,
        strategy=strategy,
    )
    wall_ms = (time.perf_counter() - t0) * 1000

    chunks = result.get("retrieved_chunks", [])
    scores = [c["relevance_score"] for c in chunks]

    # Metadata completeness check
    metadata_issues: List[str] = []
    for i, c in enumerate(chunks):
        meta = c.get("metadata", {})
        missing = REQUIRED_METADATA_KEYS - set(meta.keys())
        if missing:
            metadata_issues.append(f"chunk[{i}] missing keys: {missing}")

    return {
        "query": query,
        "strategy": strategy,
        "top_k": top_k,
        "match_threshold": match_threshold,
        "section_filter": section_filter,
        "wall_ms": round(wall_ms, 1),
        "timing": result.get("timing", {}),
        "chunk_count": len(chunks),
        "scores": scores,
        "score_min": round(min(scores), 4) if scores else None,
        "score_max": round(max(scores), 4) if scores else None,
        "score_mean": round(statistics.mean(scores), 4) if scores else None,
        "metadata_issues": metadata_issues,
        "section_labels": [c.get("metadata", {}).get("section_label") for c in chunks],
    }


def run_evaluation(
    user_id: str,
    queries: List[str],
    strategies: List[str],
    top_k: int,
    thresholds: List[float],
) -> List[Dict[str, Any]]:
    """Run the full evaluation matrix: queries × strategies × thresholds."""
    all_results: List[Dict[str, Any]] = []

    total = len(queries) * len(strategies) * len(thresholds)
    logger.info(
        "Starting evaluation: %d queries × %d strategies × %d thresholds = %d runs",
        len(queries), len(strategies), len(thresholds), total,
    )

    for threshold in thresholds:
        for strategy in strategies:
            for query in queries:
                try:
                    result = run_single_query(
                        user_id=user_id,
                        query=query,
                        strategy=strategy,
                        top_k=top_k,
                        match_threshold=threshold,
                    )
                    all_results.append(result)
                    logger.info(
                        "  %-8s thr=%.2f chunks=%2d score_mean=%s wall_ms=%6.1f | %s",
                        strategy,
                        threshold,
                        result["chunk_count"],
                        result["score_mean"],
                        result["wall_ms"],
                        query[:60],
                    )
                except Exception as exc:
                    logger.error("FAILED: strategy=%s query=%s: %s", strategy, query, exc)
                    all_results.append({
                        "query": query,
                        "strategy": strategy,
                        "match_threshold": threshold,
                        "error": str(exc),
                    })

    return all_results


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print a human-readable evaluation summary."""
    print("\n" + "=" * 80)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("=" * 80)

    # Group by strategy
    by_strategy: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        s = r.get("strategy", "unknown")
        by_strategy.setdefault(s, []).append(r)

    for strategy, runs in by_strategy.items():
        successful = [r for r in runs if "error" not in r]
        failed = [r for r in runs if "error" in r]

        print(f"\n── Strategy: {strategy} ({'─' * 50})")
        print(f"   Runs: {len(runs)} ({len(successful)} ok, {len(failed)} failed)")

        if successful:
            latencies = [r["wall_ms"] for r in successful]
            chunk_counts = [r["chunk_count"] for r in successful]
            all_scores = [s for r in successful for s in r.get("scores", [])]

            print(f"   Latency   — min: {min(latencies):.1f}ms  "
                  f"mean: {statistics.mean(latencies):.1f}ms  "
                  f"max: {max(latencies):.1f}ms  "
                  f"p95: {sorted(latencies)[int(len(latencies) * 0.95)]:.1f}ms")
            print(f"   Chunks    — min: {min(chunk_counts)}  "
                  f"mean: {statistics.mean(chunk_counts):.1f}  "
                  f"max: {max(chunk_counts)}")
            if all_scores:
                print(f"   Scores    — min: {min(all_scores):.4f}  "
                      f"mean: {statistics.mean(all_scores):.4f}  "
                      f"max: {max(all_scores):.4f}")

            # Metadata quality
            issues = [iss for r in successful for iss in r.get("metadata_issues", [])]
            if issues:
                print(f"   Metadata  — {len(issues)} issue(s):")
                for iss in issues[:5]:
                    print(f"     ⚠ {iss}")
            else:
                print("   Metadata  — ✓ all chunks have complete metadata")

        if failed:
            print(f"   Failures:")
            for f in failed:
                print(f"     ✗ {f['query'][:50]}: {f['error']}")

    print("\n" + "=" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Week-4 Retrieval Optimization — evaluation script"
    )
    parser.add_argument("--user-id", required=True, help="UUID of the user to query")
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=["pgvector"],
        choices=["pgvector", "faiss"],
        help="Retrieval strategies to benchmark",
    )
    parser.add_argument("--top-k", type=int, default=10, help="Max chunks per query")
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=float,
        default=[0.4],
        help="Match thresholds to sweep (e.g. 0.3 0.4 0.5)",
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        default=None,
        help="Custom queries (uses built-in medical queries if omitted)",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Path to write detailed JSON results",
    )
    args = parser.parse_args()

    queries = args.queries or DEFAULT_QUERIES

    results = run_evaluation(
        user_id=args.user_id,
        queries=queries,
        strategies=args.strategies,
        top_k=args.top_k,
        thresholds=args.thresholds,
    )

    print_summary(results)

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("Detailed results written to %s", args.output_json)


if __name__ == "__main__":
    main()
