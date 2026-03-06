"""End-to-end RAG ingestion script: Supabase OCR → clean → chunk → embed → upsert.

This is the Week-2 deliverable for populating the first real vector DB.

What it does
------------
1) Fetches OCR'd reports (rows in `medical_reports`) for a given `user_id`
2) Indexes each report into `report_chunks` via `index_report`
3) Optionally runs a sample retrieval query to verify vectors are queryable

Run (from `src/`):
  python -m backend.scripts.ingest_supabase_reports --user-id <uuid> --limit 3 --verify-query "Why is my iron low?"

Prereqs
-------
- Env vars set: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
- DB migrations applied:
    - src/db/migrations/001_add_report_chunks.sql
    - src/db/migrations/002_add_report_chunk_metadata.sql
- At least N reports already OCR'd (have rows in `medical_reports` with `ocr_text`).
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from backend.config.supabase_client import get_supabase_client
from backend.services.retrieval import index_report, retrieve_pgvector


def _fetch_reports_for_user(
    user_id: str,
    *,
    limit: int,
    report_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    client = get_supabase_client()

    q = (
        client.table("medical_reports")
        .select("id, user_id, ocr_text, source_file_name, source_url, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )

    if report_ids:
        q = q.in_("id", report_ids)

    res = q.limit(limit).execute()
    return res.data or []


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate Supabase vector store from OCR'd reports")
    parser.add_argument("--user-id", required=True, help="User UUID (owner of the reports)")
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Number of most-recent OCR'd reports to index (default: 3)",
    )
    parser.add_argument(
        "--report-id",
        action="append",
        default=None,
        help="Specific report UUID to index (can be repeated). If provided, overrides --limit selection.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=300,
        help="Chunk size in characters (default: 300)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Chunk overlap in characters (default: 50)",
    )
    parser.add_argument(
        "--verify-query",
        default=None,
        help="If provided, runs a pgvector retrieval query after indexing to verify queryability.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-k chunks to return in verification query (default: 5)",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.4,
        help="Cosine similarity threshold for verification query (default: 0.4)",
    )

    args = parser.parse_args()

    report_ids = args.report_id
    effective_limit = len(report_ids) if report_ids else args.limit

    reports = _fetch_reports_for_user(
        args.user_id,
        limit=effective_limit,
        report_ids=report_ids,
    )

    if not reports:
        print("❌ No OCR'd reports found for user. Ensure OCR has been run and medical_reports rows exist.")
        return

    distinct_reports = {r.get("id") for r in reports if r.get("id")}
    print(f"Found {len(distinct_reports)} report(s) to index")

    total_chunks = 0
    for r in reports:
        report_id = r.get("id")
        ocr_text = r.get("ocr_text") or ""
        source_filename = r.get("source_file_name")
        source_url = r.get("source_url")

        if not report_id:
            continue
        if not ocr_text.strip():
            print(f"⚠️  Skipping report {report_id}: empty OCR text")
            continue

        n = index_report(
            report_id=report_id,
            user_id=args.user_id,
            ocr_text=ocr_text,
            source_filename=source_filename,
            source_url=source_url,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        total_chunks += n
        print(f"✅ Indexed report {report_id}: {n} chunk(s)")

    print(f"\nDone. Total chunks indexed: {total_chunks}")

    if args.verify_query:
        print("\nVerifying retrieval via pgvector RPC...")
        results = retrieve_pgvector(
            user_id=args.user_id,
            query=args.verify_query,
            top_k=args.top_k,
            match_threshold=args.match_threshold,
        )
        print(f"Retrieved {len(results)} chunk(s)")
        for i, item in enumerate(results, start=1):
            meta = item.get("metadata") or {}
            print(f"\n--- RESULT {i} ---")
            print("score:", item.get("relevance_score"))
            print("text:", (item.get("text_content") or "")[:250])
            print("source_filename:", meta.get("source_filename"))
            print("source_url:", meta.get("source_url"))
            print("page_number:", meta.get("page_number"))


if __name__ == "__main__":
    main()
