#!/usr/bin/env python3
"""End-to-end test for document-2.pdf: Upload → OCR → Gemini Extraction → DB Verification.

This script:
  1. Uploads document-2.pdf to Supabase Storage via POST /reports/process
  2. Prints the OCR text extracted by Tesseract
  3. Prints every lab result Gemini extracted
  4. Queries the database directly to verify the rows landed in medical_reports + lab_results
  5. Prints a formatted table of all lab results from the DB

Usage:
    # Start the backend server first:
    #   cd src && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

    cd src/backend
    python test_document2.py
"""

import json
import os
import sys
import time
import uuid

import requests

# ── Configuration ─────────────────────────────────────────────────────────────

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
UPLOAD_URL = f"{BASE_URL}/reports/upload"
OCR_URL = f"{BASE_URL}/reports/ocr"
EXTRACT_GEMINI_URL = f"{BASE_URL}/reports/extract-labs-gemini"
PROCESS_URL = f"{BASE_URL}/reports/process"

# Resolve document-2.pdf relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
PDF_PATH = os.path.join(PROJECT_ROOT, "docs", "document-2.pdf")

USER_ID = os.getenv("USER_ID", str(uuid.uuid4()))

# ── Colours for terminal output ───────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def banner(title: str) -> None:
    width = 70
    print(f"\n{CYAN}{BOLD}{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}{RESET}\n")


def success(msg: str) -> None:
    print(f"  {GREEN}✅ {msg}{RESET}")


def fail(msg: str) -> None:
    print(f"  {RED}❌ {msg}{RESET}")


def info(msg: str) -> None:
    print(f"  {YELLOW}ℹ  {msg}{RESET}")


def section(title: str) -> None:
    print(f"\n  {BOLD}── {title} {'─' * (50 - len(title))}{RESET}")


# ── Step 1: Full pipeline (upload + OCR + Gemini) ────────────────────────────

def run_full_pipeline() -> dict:
    """Upload document-2.pdf through the full /reports/process endpoint."""
    banner("STEP 1: Full Pipeline — Upload → OCR → Gemini Extraction")

    if not os.path.exists(PDF_PATH):
        fail(f"PDF not found at: {PDF_PATH}")
        sys.exit(1)

    info(f"PDF path:  {PDF_PATH}")
    info(f"File size: {os.path.getsize(PDF_PATH):,} bytes")
    info(f"User ID:   {USER_ID}")
    info(f"Server:    {BASE_URL}")

    print()
    info("Sending to POST /reports/process ...")

    start = time.time()
    with open(PDF_PATH, "rb") as f:
        resp = requests.post(
            PROCESS_URL,
            data={"user_id": USER_ID},
            files={"file": ("document-2.pdf", f, "application/pdf")},
            timeout=120,
        )
    elapsed = time.time() - start

    if resp.status_code not in (200, 201):
        fail(f"Pipeline failed: HTTP {resp.status_code}")
        print(f"  Response: {resp.text[:500]}")
        sys.exit(1)

    result = resp.json()
    success(f"Pipeline completed in {elapsed:.1f}s")
    info(f"Report ID:      {result.get('report_id')}")
    info(f"Storage path:   {result.get('storage_path')}")
    info(f"OCR confidence: {result.get('ocr_confidence')}")

    if result.get("extraction_error"):
        fail(f"Extraction error: {result['extraction_error']}")
    else:
        extraction = result.get("extraction", {})
        success(f"Labs inserted: {extraction.get('inserted', 0)}")
        info(f"Labs skipped:  {extraction.get('skipped', 0)}")

    return result


# ── Step 2: Print OCR text ───────────────────────────────────────────────────

def print_ocr_text(result: dict) -> None:
    """Print the OCR text preview from the pipeline result."""
    banner("STEP 2: OCR Text (preview)")

    preview = result.get("ocr_text_preview", "")
    if preview:
        print(preview)
        if len(preview) >= 500:
            info("(truncated to 500 chars — full text is stored in the DB)")
    else:
        info("No OCR text preview in response.")


# ── Step 3: Print Gemini extraction details ──────────────────────────────────

def print_extraction_details(result: dict) -> None:
    """Print every lab result that Gemini extracted."""
    banner("STEP 3: Gemini Extraction Results")

    extraction = result.get("extraction", {})
    if not extraction:
        info("No extraction data (check extraction_error in the response).")
        return

    # Metadata
    metadata = extraction.get("metadata_updates", {})
    if metadata:
        section("Report Metadata Updates")
        for k, v in metadata.items():
            info(f"{k}: {v}")

    # Gemini notes
    notes = extraction.get("gemini_notes")
    if notes:
        section("Gemini Notes")
        print(f"  {notes}")

    # Extraction log
    log_data = extraction.get("extraction_log", {})
    if log_data:
        section("Extraction Summary")
        info(f"Total tests found: {log_data.get('total_tests_found', '?')}")
        info(f"Tests inserted:    {log_data.get('tests_inserted', '?')}")
        info(f"Tests skipped:     {log_data.get('tests_skipped', '?')}")

        if log_data.get("skipped_details"):
            section("Skipped Details")
            for reason in log_data["skipped_details"]:
                print(f"    ⏭  {reason}")

        if log_data.get("warnings"):
            section("Warnings")
            for w in log_data["warnings"]:
                print(f"    ⚠  {w}")

        if log_data.get("errors"):
            section("Errors")
            for e in log_data["errors"]:
                print(f"    ❌ {e}")


# ── Step 4: Verify data in the database ──────────────────────────────────────

def verify_database(report_id: str) -> None:
    """Query Supabase directly to verify the rows landed in the DB."""
    banner("STEP 4: Database Verification")

    # Import Supabase client (uses the same .env as the server)
    sys.path.insert(0, os.path.join(SCRIPT_DIR, ".."))
    from dotenv import load_dotenv
    # Try backend/.env first (where user keeps creds), then project root
    load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        fail("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set in .env")
        return

    client = create_client(url, key)

    # ── Check medical_reports row ─────────────────────────────────────────
    section("medical_reports")
    try:
        mr_resp = (
            client.table("medical_reports")
            .select("id, user_id, report_date, report_type, source_file_name, ocr_engine, ocr_confidence, created_at")
            .eq("id", report_id)
            .execute()
        )
    except Exception as exc:
        fail(f"Query failed: {exc}")
        return

    mr_data = mr_resp.data or []
    if not mr_data:
        fail(f"No medical_reports row found for report_id={report_id}")
        return

    row = mr_data[0]
    success("medical_reports row found:")
    for k, v in row.items():
        print(f"    {k:25s} = {v}")

    # ── Fetch full OCR text length ────────────────────────────────────────
    ocr_resp = (
        client.table("medical_reports")
        .select("ocr_text")
        .eq("id", report_id)
        .execute()
    )
    ocr_text = (ocr_resp.data or [{}])[0].get("ocr_text", "")
    info(f"OCR text length: {len(ocr_text):,} characters")

    # ── Check lab_results rows ────────────────────────────────────────────
    section("lab_results")
    try:
        lr_resp = (
            client.table("lab_results")
            .select("id, test_name, value, unit, reference_range, abnormal_flag, extracted_from_page")
            .eq("report_id", report_id)
            .order("test_name")
            .execute()
        )
    except Exception as exc:
        fail(f"Query failed: {exc}")
        return

    labs = lr_resp.data or []
    if not labs:
        fail("No lab_results rows found for this report.")
        return

    success(f"{len(labs)} lab_results rows found\n")

    # Pretty-print as a table
    header = f"  {'#':>3}  {'Test Name':<35} {'Value':>10} {'Unit':<15} {'Ref Range':<20} {'Abnormal':>8}  {'Page':>4}"
    separator = f"  {'─' * 3}  {'─' * 35} {'─' * 10} {'─' * 15} {'─' * 20} {'─' * 8}  {'─' * 4}"
    print(header)
    print(separator)

    abnormal_count = 0
    for i, lab in enumerate(labs, 1):
        val = lab.get("value")
        val_str = f"{val}" if val is not None else "—"
        unit = lab.get("unit") or "—"
        ref = lab.get("reference_range") or "—"
        abn = lab.get("abnormal_flag")
        abn_str = "YES" if abn is True else ("no" if abn is False else "—")
        page = lab.get("extracted_from_page")
        page_str = str(page) if page is not None else "—"

        # Highlight abnormal values
        line_color = RED if abn is True else ""
        line_reset = RESET if abn is True else ""

        if abn is True:
            abnormal_count += 1

        print(
            f"  {line_color}{i:>3}  {lab['test_name']:<35} {val_str:>10} {unit:<15} {ref:<20} {abn_str:>8}  {page_str:>4}{line_reset}"
        )

    print(separator)
    print()
    success(f"Total: {len(labs)} tests  |  Abnormal: {abnormal_count}  |  Normal: {len(labs) - abnormal_count}")


# ── Step 5: Full OCR text dump ───────────────────────────────────────────────

def print_full_ocr_text(report_id: str) -> None:
    """Optionally fetch and print the complete OCR text from the DB."""
    banner("STEP 5: Full OCR Text from Database")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return

    client = create_client(url, key)
    resp = (
        client.table("medical_reports")
        .select("ocr_text")
        .eq("id", report_id)
        .execute()
    )
    ocr_text = (resp.data or [{}])[0].get("ocr_text", "")
    if ocr_text:
        print(ocr_text[:3000])
        if len(ocr_text) > 3000:
            info(f"(showing 3000/{len(ocr_text)} chars — full text in DB)")
    else:
        info("No OCR text found.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    banner("TEST: document-2.pdf → Full Pipeline → Database Verification")
    info(f"PDF:    {PDF_PATH}")
    info(f"Server: {BASE_URL}")

    # Check server is up
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            success("Server is healthy")
        else:
            fail(f"Server returned {health.status_code}")
            sys.exit(1)
    except requests.ConnectionError:
        fail(f"Cannot connect to {BASE_URL} — is the server running?")
        info("Start it with: cd src && uvicorn backend.main:app --reload --port 8000")
        sys.exit(1)

    # Run pipeline
    result = run_full_pipeline()
    report_id = result.get("report_id")

    if not report_id:
        fail("No report_id returned — cannot verify DB.")
        sys.exit(1)

    # Print outputs
    print_ocr_text(result)
    print_extraction_details(result)
    verify_database(report_id)

    # Print full OCR text if --ocr flag passed
    if "--ocr" in sys.argv:
        print_full_ocr_text(report_id)

    # Final summary
    banner("TEST COMPLETE")
    extraction = result.get("extraction", {})
    if result.get("extraction_error"):
        fail(f"Extraction had an error: {result['extraction_error']}")
    elif extraction.get("inserted", 0) > 0:
        success(f"document-2.pdf processed successfully!")
        success(f"Report ID:    {report_id}")
        success(f"Labs inserted: {extraction.get('inserted')}")
        info(f"Labs skipped:  {extraction.get('skipped', 0)}")
    else:
        info("Pipeline ran but no lab results were inserted.")

    print()
    info("To see full OCR text, re-run with: python test_document2.py --ocr")
    info(f"To view in Supabase dashboard: Table Editor → medical_reports → filter id = {report_id}")
    print()


if __name__ == "__main__":
    main()
