#!/usr/bin/env python3
"""End-to-end pipeline test: Ingest → Poll → RAG query.

Picks a random PDF from ``src/sample_reports/``, uploads it via
``POST /reports/ingest``, polls ``GET /reports/status/{id}`` until the
pipeline completes (OCR → regex → RAG indexing → Gemini extraction), then
fires a ``POST /api/v1/rag_query`` to verify that chunks were indexed and
are retrievable.

Usage
-----
1.  Start the server (from ``src/``):

        PYTHONPATH=. uvicorn backend.main:app --reload --port 8000

2.  Run this script (from ``src/``):

        PYTHONPATH=. python backend/scripts/test_full_pipeline.py

    Or with a specific report:

        PYTHONPATH=. python backend/scripts/test_full_pipeline.py \\
            --report sample_reports/diabetes/diabetes__Ramesh_Kumar__52M.pdf

    Or against a different host/port:

        PYTHONPATH=. python backend/scripts/test_full_pipeline.py --base-url http://localhost:9000
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import uuid
from pathlib import Path

import requests

# ── Defaults ──────────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
SAMPLE_REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "sample_reports"
POLL_INTERVAL = 3          # seconds between status polls
POLL_TIMEOUT  = 300        # max seconds to wait for pipeline completion

# ── Colour helpers (ANSI) ────────────────────────────────────────────────────

_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"
_CYAN   = "\033[96m"
_BOLD   = "\033[1m"
_RESET  = "\033[0m"

def _ok(msg: str)   -> None: print(f"{_GREEN}✓ {msg}{_RESET}")
def _warn(msg: str)  -> None: print(f"{_YELLOW}⚠ {msg}{_RESET}")
def _fail(msg: str)  -> None: print(f"{_RED}✗ {msg}{_RESET}")
def _info(msg: str)  -> None: print(f"{_CYAN}ℹ {msg}{_RESET}")
def _head(msg: str)  -> None: print(f"\n{_BOLD}{'═'*60}\n  {msg}\n{'═'*60}{_RESET}")


# ── Step helpers ──────────────────────────────────────────────────────────────

def pick_random_report(reports_dir: Path) -> Path:
    """Walk sample_reports/ and return a random PDF path."""
    pdfs = sorted(reports_dir.rglob("*.pdf"))
    if not pdfs:
        _fail(f"No PDFs found under {reports_dir}")
        sys.exit(1)
    chosen = random.choice(pdfs)
    _info(f"Selected report: {chosen.relative_to(reports_dir.parent)}")
    return chosen


def health_check(base_url: str) -> None:
    """Verify the server is reachable."""
    url = f"{base_url}/health"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        _ok(f"Server healthy at {base_url}")
    except requests.RequestException as exc:
        _fail(f"Cannot reach {url} — is the server running?\n  {exc}")
        sys.exit(1)


def ingest_report(base_url: str, pdf_path: Path, user_id: str) -> dict:
    """POST /reports/ingest and return the JSON response."""
    url = f"{base_url}/reports/ingest"
    user_name = pdf_path.stem.split("__")[1] if "__" in pdf_path.stem else "Test User"

    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        data  = {"user_id": user_id, "user_name": user_name}
        _info(f"POST {url}")
        _info(f"  user_id   = {user_id}")
        _info(f"  user_name = {user_name}")
        _info(f"  file      = {pdf_path.name}")
        r = requests.post(url, data=data, files=files, timeout=30)

    if r.status_code not in (200, 201, 202):
        _fail(f"Ingest failed ({r.status_code}): {r.text[:500]}")
        sys.exit(1)

    body = r.json()
    _ok(f"Ingest accepted — report_id = {body['report_id']}")
    _info(f"  storage_path = {body.get('storage_path', 'n/a')}")
    _info(f"  status       = {body.get('processing_status', 'n/a')}")
    return body


def poll_status(base_url: str, report_id: str) -> dict:
    """Poll GET /reports/status/{report_id} until done/failed or timeout."""
    url = f"{base_url}/reports/status/{report_id}"
    _info(f"Polling {url} (every {POLL_INTERVAL}s, timeout {POLL_TIMEOUT}s) …")

    start = time.time()
    last_status = ""

    while True:
        elapsed = time.time() - start
        if elapsed > POLL_TIMEOUT:
            _fail(f"Pipeline timed out after {POLL_TIMEOUT}s (last status: {last_status})")
            sys.exit(1)

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            body = r.json()
        except requests.RequestException as exc:
            _warn(f"Poll request failed ({exc}), retrying …")
            time.sleep(POLL_INTERVAL)
            continue

        current_status = body.get("processing_status", "unknown")
        if current_status != last_status:
            _info(f"  [{elapsed:5.1f}s] status → {current_status}")
            last_status = current_status

        if current_status == "done":
            _ok(f"Pipeline completed in {elapsed:.1f}s")
            _info(f"  lab_results_count = {body.get('lab_results_count', 'n/a')}")
            _info(f"  ocr_confidence    = {body.get('ocr_confidence', 'n/a')}")
            return body

        if current_status == "failed":
            _fail(f"Pipeline failed: {body.get('processing_error', 'unknown error')}")
            # Don't exit — let the RAG test still run to check if partial data exists.
            return body

        time.sleep(POLL_INTERVAL)


def check_lab_results(base_url: str, report_id: str, user_id: str) -> int:
    """Query lab_results via API endpoint, with direct-DB fallback."""
    # ── Try HTTP API first (always works, no module import needed) ────────
    try:
        url = f"{base_url}/reports/{report_id}/lab-results"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            body = r.json()
            rows = body.get("lab_results", [])
            count = body.get("count", len(rows))
            if count > 0:
                _ok(f"Found {count} lab results via API for this report:")
                for row in rows[:15]:
                    flag = " ⚠ ABNORMAL" if row.get("abnormal_flag") else ""
                    _info(f"    {row['test_name']}: {row['value']} {row.get('unit', '')}{flag}")
                if count > 15:
                    _info(f"    … and {count - 15} more")
            else:
                _warn("No lab_results rows found for this report (via API)")
            return count
    except Exception as exc:
        _warn(f"API lab-results check failed: {exc}")

    # ── Fallback: direct Supabase client ─────────────────────────────────
    try:
        from backend.config.supabase_client import get_supabase_client
        client = get_supabase_client()
        resp = (
            client.table("lab_results")
            .select("test_name, value, unit, abnormal_flag", count="exact")
            .eq("report_id", report_id)
            .execute()
        )
        rows = resp.data or []
        count = len(rows)
        if count > 0:
            _ok(f"Found {count} lab results in DB for this report:")
            for row in rows[:15]:
                flag = " ⚠ ABNORMAL" if row.get("abnormal_flag") else ""
                _info(f"    {row['test_name']}: {row['value']} {row.get('unit', '')}{flag}")
            if count > 15:
                _info(f"    … and {count - 15} more")
        else:
            _warn("No lab_results rows found for this report")
        return count
    except Exception as exc:
        _warn(f"Could not query lab_results directly: {exc}")
        return 0


def check_rag_chunks(report_id: str, status_resp: dict | None = None) -> int:
    """Query report_chunks directly to verify indexing."""
    # ── Fallback: use status API lab_results_count as proxy ────────────────
    # (If we can't query the DB, the status endpoint already confirmed results.)
    try:
        from backend.config.supabase_client import get_supabase_client
        client = get_supabase_client()

        # Try querying with Week-3 metadata columns first; fall back to base columns
        # if they don't exist (migration 003 not yet applied).
        has_week3 = True
        try:
            resp = (
                client.table("report_chunks")
                .select("id, chunk_index, section_label, embedding_version", count="exact")
                .eq("report_id", report_id)
                .execute()
            )
        except Exception:
            has_week3 = False
            resp = (
                client.table("report_chunks")
                .select("id, chunk_index", count="exact")
                .eq("report_id", report_id)
                .execute()
            )

        rows = resp.data or []
        count = len(rows)
        if count > 0:
            _ok(f"Found {count} RAG chunks in DB for this report:")
            if has_week3:
                section_counts: dict[str, int] = {}
                for row in rows:
                    lbl = row.get("section_label", "other")
                    section_counts[lbl] = section_counts.get(lbl, 0) + 1
                for lbl, cnt in sorted(section_counts.items()):
                    _info(f"    {lbl}: {cnt} chunks")
                _info(f"    embedding_version = {rows[0].get('embedding_version', 'n/a')}")
            else:
                _info("    (Week-3 metadata columns not available — base schema only)")
        else:
            _warn("No report_chunks rows found — RAG indexing may have failed")
        return count
    except Exception as exc:
        _warn(f"Could not query report_chunks directly: {exc}")
        # If the status response already confirmed the pipeline is done,
        # assume chunks exist (RAG query in step 5 will verify).
        if status_resp and status_resp.get("processing_status") == "done":
            _info("  (Pipeline status=done; RAG query in Step 5 will verify chunk retrieval)")
            return -1  # sentinel: unknown but pipeline succeeded
        return 0


def rag_query(base_url: str, user_id: str, query: str) -> dict:
    """POST /api/v1/rag_query and return the response."""
    url = f"{base_url}/api/v1/rag_query"
    payload = {
        "user_id": user_id,
        "query": query,
        "role": "user",
        "retrieval_strategy": "pgvector",
        "top_k": 5,
        "match_threshold": 0.3,
    }
    _info(f"POST {url}")
    _info(f"  query = \"{query}\"")

    try:
        r = requests.post(url, json=payload, timeout=60)
    except requests.RequestException as exc:
        _fail(f"RAG query request failed: {exc}")
        return {}

    if r.status_code != 200:
        _fail(f"RAG query returned {r.status_code}: {r.text[:500]}")
        return {}

    body = r.json()
    return body


def display_rag_result(result: dict) -> None:
    """Pretty-print the RAG query response."""
    chunks_n = result.get("chunks_retrieved", 0)
    grounding = result.get("grounding_available", False)

    if grounding and chunks_n > 0:
        _ok(f"RAG retrieval successful — {chunks_n} chunks grounded the answer")
    elif chunks_n > 0:
        _warn(f"Got {chunks_n} chunks but grounding_available={grounding}")
    else:
        _fail("No chunks retrieved — RAG pipeline may not be working")

    # Show chunk details from context
    ctx = result.get("context", {})
    rag_kb = ctx.get("rag_knowledge_base", {})
    chunks = rag_kb.get("retrieved_chunks", [])
    if chunks:
        _info(f"  Retrieved {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks[:5]):
            similarity = chunk.get("similarity", chunk.get("score", "n/a"))
            section = chunk.get("section_label", "n/a")
            text_preview = chunk.get("chunk_text", "")[:120].replace("\n", " ")
            _info(f"    [{i+1}] sim={similarity}  section={section}")
            _info(f"        \"{text_preview}…\"")

    # Show the AI answer (truncated)
    answer = result.get("answer", "")
    llm_error = result.get("llm_error")
    if llm_error:
        _warn(f"LLM error (fallback answer used): {llm_error}")
    if answer:
        _info(f"  Model: {result.get('model', 'n/a')}")
        preview = answer[:400].replace("\n", "\n    ")
        print(f"\n{_CYAN}  ── AI Answer (preview) ──{_RESET}")
        print(f"    {preview}")
        if len(answer) > 400:
            print(f"    … ({len(answer) - 400} more chars)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="End-to-end pipeline test")
    parser.add_argument(
        "--report", type=str, default=None,
        help="Path to a specific PDF to upload (default: random from sample_reports/)",
    )
    parser.add_argument(
        "--base-url", type=str, default=BASE_URL,
        help=f"Server base URL (default: {BASE_URL})",
    )
    parser.add_argument(
        "--user-id", type=str, default=None,
        help="Use a specific user UUID (default: random)",
    )
    parser.add_argument(
        "--query", type=str, default=None,
        help="Custom RAG query (default: auto-generated from report category)",
    )
    parser.add_argument(
        "--timeout", type=int, default=POLL_TIMEOUT,
        help=f"Max seconds to wait for pipeline (default: {POLL_TIMEOUT})",
    )
    args = parser.parse_args()

    # ── Setup ─────────────────────────────────────────────────────────────────
    _head("FULL PIPELINE TEST")

    user_id = args.user_id or str(uuid.uuid4())

    if args.report:
        pdf_path = Path(args.report)
        if not pdf_path.is_absolute():
            pdf_path = Path.cwd() / pdf_path
        if not pdf_path.exists():
            _fail(f"Report not found: {pdf_path}")
            sys.exit(1)
        _info(f"Using specified report: {pdf_path.name}")
    else:
        if not SAMPLE_REPORTS_DIR.exists():
            _fail(f"sample_reports/ not found at {SAMPLE_REPORTS_DIR}")
            sys.exit(1)
        pdf_path = pick_random_report(SAMPLE_REPORTS_DIR)

    # Derive category from folder name for smarter RAG query
    category = pdf_path.parent.name if pdf_path.parent.name != "sample_reports" else "general"

    # Build a relevant RAG query based on report category
    CATEGORY_QUERIES = {
        "diabetes":           "What are my blood sugar and HbA1c levels? Am I diabetic?",
        "pre_diabetes":       "Are my glucose levels indicating pre-diabetes?",
        "anaemia_b12":        "What are my hemoglobin and B12 levels? Do I have anemia?",
        "iron_deficiency":    "What are my iron and ferritin levels?",
        "hypothyroidism":     "What are my thyroid function test results?",
        "hyperthyroidism":    "Are my thyroid hormone levels elevated?",
        "high_cholesterol":   "What are my cholesterol and lipid profile results?",
        "cardiac_risk":       "What is my cardiac risk based on the report?",
        "liver_disease":      "What are my liver function test results?",
        "ckd_early":          "What are my kidney function results including creatinine and eGFR?",
        "metabolic_syndrome": "Do I have metabolic syndrome based on my lab results?",
        "healthy":            "Summarise my overall health based on this report.",
        "autoimmune":         "Are there any autoimmune markers in my results?",
        "osteoporosis_risk":  "What are my calcium and vitamin D levels?",
        "pcos":               "What are my hormone levels? Any signs of PCOS?",
        "vit_d_deficiency":   "What are my vitamin D levels?",
        "multi_condition":    "Give me an overall summary of all my lab results.",
    }
    rag_query_text = args.query or CATEGORY_QUERIES.get(category, "Summarise my lab results and health status.")

    # ── Step 0: Health check ──────────────────────────────────────────────────
    _head("STEP 0 — Health Check")
    health_check(args.base_url)

    # ── Step 1: Ingest ────────────────────────────────────────────────────────
    _head("STEP 1 — Ingest Report")
    ingest_resp = ingest_report(args.base_url, pdf_path, user_id)
    report_id = ingest_resp["report_id"]

    # ── Step 2: Poll until done ───────────────────────────────────────────────
    _head("STEP 2 — Poll Pipeline Status")
    status_resp = poll_status(args.base_url, report_id)
    pipeline_status = status_resp.get("processing_status", "unknown")

    # ── Step 3: Verify lab results ────────────────────────────────────────────
    _head("STEP 3 — Verify Lab Results")
    lab_count = check_lab_results(args.base_url, report_id, user_id)
    # If the API check failed but status reported a count, use that.
    if lab_count == 0 and status_resp.get("lab_results_count"):
        lab_count = status_resp["lab_results_count"]
        _info(f"  (Using lab_results_count={lab_count} from status endpoint)")

    # ── Step 4: Verify RAG chunks ─────────────────────────────────────────
    _head("STEP 4 — Verify RAG Chunks")
    chunk_count = check_rag_chunks(report_id, status_resp=status_resp)

    # ── Step 5: RAG query ─────────────────────────────────────────────────────
    _head("STEP 5 — RAG Query")
    _info(f"Category: {category}")
    rag_result = rag_query(args.base_url, user_id, rag_query_text)
    if rag_result:
        display_rag_result(rag_result)

    # ── Summary ───────────────────────────────────────────────────────────────
    _head("TEST SUMMARY")
    print()

    results = {
        "Report":          pdf_path.name,
        "Category":        category,
        "User ID":         user_id,
        "Report ID":       report_id,
        "Pipeline Status": pipeline_status,
        "Lab Results":     lab_count,
        "RAG Chunks":      chunk_count if chunk_count >= 0 else "n/a (DB check skipped)",
        "RAG Retrieval":   rag_result.get("chunks_retrieved", 0) if rag_result else 0,
        "Grounding":       rag_result.get("grounding_available", False) if rag_result else False,
    }

    max_key = max(len(k) for k in results)
    for key, val in results.items():
        print(f"  {key:<{max_key+2}} {val}")

    print()
    rag_chunks_ok = chunk_count > 0 or chunk_count == -1  # -1 = DB check skipped, rely on RAG query
    rag_retrieved = rag_result.get("chunks_retrieved", 0) if rag_result else 0

    all_pass = (
        pipeline_status == "done"
        and lab_count > 0
        and (rag_chunks_ok or rag_retrieved > 0)
        and rag_retrieved > 0
    )

    if all_pass:
        _ok("ALL CHECKS PASSED — full pipeline is working end-to-end! 🎉")
    else:
        problems = []
        if pipeline_status != "done":
            problems.append(f"pipeline status is '{pipeline_status}' (expected 'done')")
        if lab_count == 0:
            problems.append("no lab results extracted")
        if not rag_chunks_ok and rag_retrieved == 0:
            problems.append("no RAG chunks indexed and no chunks retrieved")
        if rag_retrieved == 0:
            problems.append("RAG query retrieved 0 chunks")
        _fail(f"SOME CHECKS FAILED: {'; '.join(problems)}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
