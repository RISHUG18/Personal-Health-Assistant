"""Smoke test: Supabase OCR text → clean → chunk → print.

This is a developer utility (not imported by production code).

Run (from `src/`):
  python -m backend.scripts.rag_cleaning_supabase_test
"""

from __future__ import annotations

from backend.config.supabase_client import get_ocr_reports_table, get_supabase_client
from backend.services.preprocessing.chunking import doc_to_chunks
from backend.services.preprocessing.text_cleaning import clean_full_text


def fetch_ocr_text(report_id: str) -> str:
    """Fetch OCR text from the configured Supabase table."""

    client = get_supabase_client()
    table = get_ocr_reports_table()

    res = client.table(table).select("ocr_text").eq("id", report_id).execute()
    if not res.data:
        return ""

    return res.data[0].get("ocr_text") or ""


def main() -> None:
    print("\nEnter report_id from Supabase:")
    report_id = input(">> ").strip()

    raw = fetch_ocr_text(report_id)
    if not raw:
        print("\n❌ No OCR text found for this ID")
        return

    print("\n===== OCR TEXT (first 500 chars) =====\n")
    print(raw[:500])
    print("\n======================================\n")

    cleaned = clean_full_text(raw)
    print("\n===== CLEANED LENGTH =====")
    print(len(cleaned))
    print("==========================\n")

    chunks = doc_to_chunks(cleaned)
    print("\nTOTAL CHUNKS:", len(chunks))

    for i, chunk in enumerate(chunks[:10]):
        print(f"\n--- CHUNK {i + 1} ---")
        print(chunk)


if __name__ == "__main__":
    main()
