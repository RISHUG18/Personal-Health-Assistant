#!/usr/bin/env python3
"""Standalone cleaning pipeline test.

Runs the complete pipeline directly (no HTTP server required):
  1.  OCR   — Tesseract reads every page of the PDF
  2.  Gemini — LLM extracts structured lab results from OCR text
  3.  Normalize — units, dates, reference ranges cleaned/canonicalised
  4.  Insert — idempotent write to Supabase (medical_reports + lab_results)
  5.  Verify — query Supabase and print the final stored rows

──────────────────────────────────────────────────────────────────────
CONFIGURATION — edit the two variables below, then run:

    cd src
    PYTHONPATH=. python backend/scripts/cleaning_pipeline_test.py
──────────────────────────────────────────────────────────────────────
"""

import os
import sys
import time
import uuid

# ── ▼▼▼  CONFIGURE HERE  ▼▼▼ ──────────────────────────────────────────────────

# Absolute or repo-relative path to the PDF under test.
PDF_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "docs", "document-2.pdf",
)

# A stable user UUID (change this to any valid UUID for your test user).
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"

# ── ▲▲▲  END CONFIG  ▲▲▲ ──────────────────────────────────────────────────────

# Make sure `backend.*` is importable when run as `python backend/cleaning_pipeline_test.py`
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import cv2
import numpy as np
from pdf2image import convert_from_path
from supabase import create_client

from backend.ocr.preprocessor import preprocess_image
from backend.ocr.ocr_engine import run_ocr
from backend.extraction.gemini_extractor import extract_with_gemini
from backend.extraction.normalizer import (
    normalize_unit,
    normalize_date,
    normalize_test_name,
    normalize_reference_range,
)
from backend.extraction.inserter import insert_lab_results, update_report_metadata

# ── Terminal colours ───────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def banner(title: str) -> None:
    w = 72
    print(f"\n{CYAN}{BOLD}{'═' * w}")
    print(f"  {title}")
    print(f"{'═' * w}{RESET}\n")

def ok(msg: str)   -> None: print(f"  {GREEN}✅  {msg}{RESET}")
def err(msg: str)  -> None: print(f"  {RED}❌  {msg}{RESET}")
def info(msg: str) -> None: print(f"  {YELLOW}ℹ   {msg}{RESET}")
def dim(msg: str)  -> None: print(f"  {DIM}{msg}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — OCR
# ═══════════════════════════════════════════════════════════════════════════════

def step_ocr(pdf_path: str) -> tuple[str, float]:
    """Convert every PDF page to text via Tesseract. Returns (full_text, avg_confidence)."""
    banner("STEP 1 — OCR  (Tesseract)")

    pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(pdf_path):
        err(f"PDF not found: {pdf_path}")
        sys.exit(1)

    info(f"PDF path  : {pdf_path}")
    info(f"File size : {os.path.getsize(pdf_path):,} bytes")

    t0 = time.time()
    pages = convert_from_path(pdf_path)
    info(f"Pages     : {len(pages)}")

    full_text = ""
    total_conf = 0.0

    for i, pil_img in enumerate(pages, 1):
        img = np.array(pil_img)[:, :, ::-1].copy()   # PIL RGB → OpenCV BGR
        processed = preprocess_image(img)
        text, conf = run_ocr(processed)
        full_text += f"\n--- Page {i} ---\n{text}"
        total_conf += conf
        info(f"  Page {i}: {len(text):,} chars, confidence {conf:.1f}%")

    avg_conf = total_conf / len(pages)
    elapsed  = time.time() - t0

    ok(f"OCR complete in {elapsed:.1f}s — {len(full_text):,} chars total, avg confidence {avg_conf:.1f}%")
    print()
    dim("── OCR preview (first 600 chars) " + "─" * 38)
    print(full_text[:600])
    if len(full_text) > 600:
        dim(f"  … ({len(full_text):,} chars total, truncated)")

    return full_text.strip(), avg_conf


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Save OCR result to Supabase medical_reports
# ═══════════════════════════════════════════════════════════════════════════════

def step_save_ocr(db, ocr_text: str, avg_conf: float, pdf_path: str) -> str:
    """Insert a medical_reports row and return the new report_id."""
    banner("STEP 2 — Save OCR to Supabase (medical_reports)")

    report_id   = str(uuid.uuid4())
    source_name = os.path.basename(pdf_path)

    try:
        db.table("medical_reports").insert({
            "id"             : report_id,
            "user_id"        : TEST_USER_ID,
            "source_file_name": source_name,
            "ocr_text"       : ocr_text,
            "ocr_engine"     : "tesseract",
            "ocr_confidence" : avg_conf,
        }).execute()
    except Exception as exc:
        err(f"Failed to save OCR to DB: {exc}")
        sys.exit(1)

    ok(f"medical_reports row created")
    info(f"  report_id : {report_id}")
    info(f"  source    : {source_name}")
    info(f"  ocr chars : {len(ocr_text):,}")
    return report_id


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Gemini extraction (raw, before normalization)
# ═══════════════════════════════════════════════════════════════════════════════

def step_gemini(ocr_text: str):
    """Send OCR text to Gemini and return the raw GeminiExtractionResponse."""
    banner("STEP 3 — Gemini AI Extraction  (gemini-2.5-flash)")

    t0 = time.time()
    try:
        result = extract_with_gemini(ocr_text)
    except Exception as exc:
        err(f"Gemini extraction failed: {exc}")
        sys.exit(1)

    elapsed = time.time() - t0
    ok(f"Gemini extraction complete in {elapsed:.1f}s")
    info(f"  Tests found   : {len(result.lab_results)}")
    info(f"  Metadata date : {result.metadata.report_date or '—'}")
    info(f"  Metadata type : {result.metadata.report_type or '—'}")
    info(f"  Patient       : {result.metadata.patient_name or '—'}")
    info(f"  Lab           : {result.metadata.lab_name or '—'}")
    if result.extraction_notes:
        info(f"  Gemini notes  : {result.extraction_notes}")

    print()
    dim("── Raw results from Gemini (before normalization) " + "─" * 22)
    hdr = f"  {'#':>3}  {'Test Name':<38} {'Raw Value':<15} {'Raw Unit':<18} {'Raw Ref Range':<22} {'Abn':>4}"
    sep = f"  {'─'*3}  {'─'*38} {'─'*15} {'─'*18} {'─'*22} {'─'*4}"
    print(hdr)
    print(sep)
    for i, lab in enumerate(result.lab_results, 1):
        val  = str(lab.value) if lab.value is not None else (lab.value_string or "—")
        unit = lab.unit or "—"
        ref  = lab.reference_range or "—"
        abn  = ("H" if lab.is_abnormal is True else ("N" if lab.is_abnormal is False else "?"))
        print(f"  {i:>3}  {lab.test_name:<38} {val:<15} {unit:<18} {ref:<22} {abn:>4}")
    print(sep)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Normalization layer (show before → after for every field)
# ═══════════════════════════════════════════════════════════════════════════════

def step_normalize(result) -> None:
    """Print a detailed before-→-after table for every normalization applied."""
    banner("STEP 4 — Normalization Layer")

    print(f"  {BOLD}Units{RESET}  — canonicalise case/symbols, OCR noise (y→µ), trailing punctuation")
    print(f"  {BOLD}Dates{RESET}  — convert any format to ISO-8601 YYYY-MM-DD")
    print(f"  {BOLD}NULL policy{RESET} — ambiguous or missing fields stay NULL (never guessed)")
    print()

    # ── Unit normalization ────────────────────────────────────────────────────
    unit_changes = []
    unit_unchanged = []
    for lab in result.lab_results:
        raw  = lab.unit
        norm = normalize_unit(raw)
        if raw != norm:
            unit_changes.append((lab.test_name, raw, norm))
        else:
            unit_unchanged.append((lab.test_name, raw))

    if unit_changes:
        dim("  ── Units changed " + "─" * 54)
        print(f"  {'Test Name':<40} {'Raw':<20} →  {'Normalized'}")
        for name, raw, norm in unit_changes:
            null_tag = f" {RED}→ NULL{RESET}" if norm is None else ""
            norm_str = norm if norm is not None else "NULL"
            print(f"  {YELLOW}{name:<40}{RESET} {repr(raw):<20} →  {GREEN}{norm_str}{RESET}{null_tag}")
    else:
        ok("All units already in canonical form — no changes needed")

    if unit_unchanged:
        dim(f"\n  ── Units unchanged ({len(unit_unchanged)}) " + "─" * 46)
        for name, unit in unit_unchanged:
            print(f"  {DIM}  {name:<40} {unit or 'NULL'}{RESET}")

    # ── Date normalization ────────────────────────────────────────────────────
    print()
    raw_date  = result.metadata.report_date
    norm_date = normalize_date(raw_date)

    dim("  ── Date normalization " + "─" * 49)
    if raw_date is None:
        info("  report_date: not found in report → stored as NULL")
    elif norm_date is None:
        err(f"  report_date: '{raw_date}' could not be parsed → stored as NULL (ambiguous)")
    elif raw_date != norm_date:
        print(f"  report_date: {YELLOW}{repr(raw_date)}{RESET}  →  {GREEN}{norm_date}{RESET}")
    else:
        print(f"  report_date: {GREEN}{norm_date}{RESET} (already ISO-8601, no change)")

    # ── Reference range normalization ─────────────────────────────────────────
    print()
    range_changes = []
    for lab in result.lab_results:
        raw  = lab.reference_range
        norm = normalize_reference_range(raw)
        if raw != norm:
            range_changes.append((lab.test_name, raw, norm))

    if range_changes:
        dim("  ── Reference ranges trimmed " + "─" * 43)
        for name, raw, norm in range_changes:
            print(f"  {name:<40} {repr(raw)}  →  {repr(norm)}")
    else:
        dim("  ── Reference ranges: no whitespace trimming needed " + "─" * 20)

    # ── NULL summary ──────────────────────────────────────────────────────────
    print()
    null_units  = [l.test_name for l in result.lab_results if normalize_unit(l.unit) is None and l.unit is not None]
    null_values = [l.test_name for l in result.lab_results if l.value is None and not l.value_string]

    dim("  ── NULL policy summary " + "─" * 48)
    if null_units:
        for name in null_units:
            info(f"  unit for '{name}' unrecognised → stored as-is (not NULL'd)")
    if null_values:
        for name in null_values:
            err(f"  '{name}' has neither numeric nor string value → will be SKIPPED")
    if not null_units and not null_values:
        ok("No fields forced to NULL — all values were extractable")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Insert into Supabase lab_results
# ═══════════════════════════════════════════════════════════════════════════════

def step_insert(db, report_id: str, result) -> tuple[int, int]:
    """Normalise + insert into lab_results; update medical_reports metadata."""
    banner("STEP 5 — Insert to Supabase (lab_results)")

    inserted, skipped, skip_reasons = insert_lab_results(
        client=db,
        report_id=report_id,
        lab_results=result.lab_results,
    )

    if inserted:
        ok(f"Inserted {inserted} rows into lab_results")
    else:
        err("No rows inserted — check skip reasons below")

    if skipped:
        info(f"Skipped {skipped} rows:")
        for reason in skip_reasons:
            print(f"    ⏭  {reason}")

    # Update report metadata (date, type)
    updates = update_report_metadata(
        client=db,
        report_id=report_id,
        metadata=result.metadata,
    )
    if updates:
        ok("medical_reports metadata updated:")
        for k, v in updates.items():
            info(f"  {k} = {v}")
    else:
        info("No metadata updates applied (fields missing or ambiguous)")

    return inserted, skipped


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Verify: query Supabase and print the final rows
# ═══════════════════════════════════════════════════════════════════════════════

def step_verify(db, report_id: str) -> None:
    """Query Supabase and print the final stored rows."""
    banner("STEP 6 — Verification  (query Supabase)")

    # ── medical_reports ───────────────────────────────────────────────────────
    mr = (
        db.table("medical_reports")
        .select("id, user_id, report_date, report_type, source_file_name, ocr_engine, ocr_confidence, created_at")
        .eq("id", report_id)
        .execute()
    ).data or []

    if not mr:
        err(f"medical_reports row not found for report_id={report_id}")
        return

    ok("medical_reports row:")
    for k, v in mr[0].items():
        print(f"    {k:<28} = {v}")

    # ── lab_results ───────────────────────────────────────────────────────────
    labs = (
        db.table("lab_results")
        .select("test_name, value, unit, reference_range, abnormal_flag, extracted_from_page")
        .eq("report_id", report_id)
        .order("extracted_from_page", desc=False)
        .order("test_name")
        .execute()
    ).data or []

    print()
    if not labs:
        err("No lab_results rows found.")
        return

    ok(f"{len(labs)} lab_results rows stored in Supabase:\n")
    hdr = f"  {'#':>3}  {'Test Name':<38} {'Value':>10} {'Unit':<18} {'Ref Range':<25} {'Abn':>5}  {'Page':>4}"
    sep = f"  {'─'*3}  {'─'*38} {'─'*10} {'─'*18} {'─'*25} {'─'*5}  {'─'*4}"
    print(hdr)
    print(sep)

    abnormal_count = 0
    for i, lab in enumerate(labs, 1):
        val  = str(lab.get("value")) if lab.get("value") is not None else "—"
        unit = lab.get("unit") or "—"
        ref  = lab.get("reference_range") or "—"
        abn  = lab.get("abnormal_flag")
        abn_str = "YES" if abn is True else ("no" if abn is False else "—")
        page_str = str(lab.get("extracted_from_page")) if lab.get("extracted_from_page") is not None else "—"

        colour = RED if abn is True else ""
        reset  = RESET if abn is True else ""
        if abn is True:
            abnormal_count += 1

        print(f"  {colour}{i:>3}  {lab['test_name']:<38} {val:>10} {unit:<18} {ref:<25} {abn_str:>5}  {page_str:>4}{reset}")

    print(sep)
    print()
    ok(f"Total: {len(labs)} tests  |  {RED}Abnormal: {abnormal_count}{RESET}  |  Normal: {len(labs) - abnormal_count}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    banner("CLEANING PIPELINE TEST")
    info(f"PDF path : {os.path.abspath(PDF_PATH)}")
    info(f"User ID  : {TEST_USER_ID}")

    # ── Supabase client ───────────────────────────────────────────────────────
    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supa_url or not supa_key:
        err("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set in src/backend/.env")
        sys.exit(1)
    if not os.getenv("GEMINI_API_KEY"):
        err("GEMINI_API_KEY not set in src/backend/.env")
        sys.exit(1)

    db = create_client(supa_url, supa_key)
    ok("Supabase client ready")

    # ── Pipeline ──────────────────────────────────────────────────────────────
    t_total = time.time()

    ocr_text, avg_conf = step_ocr(PDF_PATH)
    report_id          = step_save_ocr(db, ocr_text, avg_conf, PDF_PATH)
    gemini_result      = step_gemini(ocr_text)
    step_normalize(gemini_result)
    inserted, skipped  = step_insert(db, report_id, gemini_result)
    step_verify(db, report_id)

    # ── Summary ───────────────────────────────────────────────────────────────
    banner("PIPELINE COMPLETE")
    ok(f"Total time   : {time.time() - t_total:.1f}s")
    ok(f"Report ID    : {report_id}")
    ok(f"Labs inserted: {inserted}")
    if skipped:
        info(f"Labs skipped : {skipped}")
    print()
    info("Re-run at any time — the insert step is idempotent (old rows are replaced).")
    info(f"Supabase dashboard → Table Editor → lab_results → filter report_id = {report_id}")
    print()


if __name__ == "__main__":
    main()
