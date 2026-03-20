"""End-to-end upload test — one call to POST /reports/ingest, then polls Supabase.

Usage
-----
1. Start the server:
       cd src
       PYTHONPATH=. uvicorn backend.main:app --reload --port 8000

2. Run this script:
       cd src
       PYTHONPATH=. python backend/scripts/test_upload.py

Optional env overrides (set before running):
    SERVER_URL     — default http://localhost:8000
    TEST_USER_ID   — default 00000000-0000-0000-0000-000000000099
    TEST_USER_NAME — default "Test User"
    PDF_PATH       — path to any PDF (default: first diabetes sample)
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# ── paths & env ────────────────────────────────────────────────────────────────
_SRC_DIR = Path(__file__).resolve().parents[2]   # src/
sys.path.insert(0, str(_SRC_DIR))

from dotenv import load_dotenv
load_dotenv(_SRC_DIR / "backend" / ".env")

# ── config ─────────────────────────────────────────────────────────────────────
SERVER_URL     = os.getenv("SERVER_URL",     "http://localhost:8000")
TEST_USER_ID   = os.getenv("TEST_USER_ID",   "00000000-0000-0000-0000-000000000099")
TEST_USER_NAME = os.getenv("TEST_USER_NAME", "Test User")
PDF_PATH       = Path(os.getenv(
    "PDF_PATH",
    str(_SRC_DIR / "sample_reports/anaemia_b12/anaemia_b12__Murugavel_P__45M.pdf"),
))
POLL_INTERVAL  = 6    # seconds between Supabase polls
MAX_WAIT       = 300  # seconds before giving up

# ── colours ────────────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"
C = "\033[96m"; B = "\033[1m";  D = "\033[2m"; X = "\033[0m"

def ok(m):   print(f"  {G}✔{X}  {m}")
def err(m):  print(f"  {R}✘{X}  {m}")
def info(m): print(f"  {Y}ℹ{X}  {m}")
def dim(m):  print(f"  {D}{m}{X}")
def banner(m):
    print(f"\n{B}{C}{'━'*60}{X}")
    print(f"{B}{C}  {m}{X}")
    print(f"{B}{C}{'━'*60}{X}\n")

# ── imports ────────────────────────────────────────────────────────────────────
try:
    import requests
except ImportError:
    err("'requests' not installed — run: pip install requests")
    sys.exit(1)

from backend.config.supabase_client import get_supabase_client

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — health check
# ══════════════════════════════════════════════════════════════════════════════
banner("VITALIS — Single-endpoint upload test")
banner("Step 1 — Server health check")

try:
    r = requests.get(f"{SERVER_URL}/health", timeout=5)
    ok(f"Server reachable → {SERVER_URL} ({r.status_code})")
except requests.exceptions.ConnectionError:
    err(f"Cannot reach server at {SERVER_URL}")
    info("Start it first:")
    dim("    cd src")
    dim("    PYTHONPATH=. uvicorn backend.main:app --reload --port 8000")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — POST /reports/ingest  (returns in <3 s with report_id)
# ══════════════════════════════════════════════════════════════════════════════
banner("Step 2 — POST /reports/ingest")

if not PDF_PATH.exists():
    err(f"PDF not found: {PDF_PATH}")
    sys.exit(1)

dim(f"File      : {PDF_PATH.name}  ({PDF_PATH.stat().st_size // 1024} KB)")
dim(f"User ID   : {TEST_USER_ID}")
dim(f"User Name : {TEST_USER_NAME}")
print()

t0 = time.time()
with PDF_PATH.open("rb") as fh:
    resp = requests.post(
        f"{SERVER_URL}/reports/ingest",
        data={"user_id": TEST_USER_ID, "user_name": TEST_USER_NAME},
        files={"file": (PDF_PATH.name, fh, "application/pdf")},
        timeout=30,
    )
elapsed = time.time() - t0

if resp.status_code not in (200, 201, 202):
    err(f"Ingest failed ({resp.status_code}) after {elapsed:.1f}s")
    print(f"  {R}{resp.text[:500]}{X}")
    sys.exit(1)

data      = resp.json()
report_id = data["report_id"]
ok(f"Accepted in {elapsed:.1f}s → HTTP {resp.status_code}")
ok(f"report_id : {report_id}")
ok(f"storage   : {data.get('storage_path', '—')}")
print()
info("Background OCR + Gemini have started. Polling Supabase for completion…")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — poll Supabase directly until the pipeline finishes
# ══════════════════════════════════════════════════════════════════════════════
banner("Step 3 — Polling Supabase for pipeline completion")

client   = get_supabase_client()
deadline = time.time() + MAX_WAIT

while time.time() < deadline:
    elapsed = time.time() - t0

    # ── fetch the medical_reports row ──────────────────────────────────────
    # Try with processing_status column first; fall back to ocr_text only
    # if migration 003 hasn't been applied.
    row = None
    try:
        row = (
            client.table("medical_reports")
            .select("ocr_text, processing_status, processing_error")
            .eq("id", report_id)
            .single()
            .execute()
        ).data
    except Exception:
        # Column might not exist — try without status columns
        try:
            row = (
                client.table("medical_reports")
                .select("ocr_text")
                .eq("id", report_id)
                .single()
                .execute()
            ).data
        except Exception as exc2:
            dim(f"  [{elapsed:>5.0f}s] DB query error: {exc2}")
            time.sleep(POLL_INTERVAL)
            continue

    if not row:
        dim(f"  [{elapsed:>5.0f}s] Row not visible yet…")
        time.sleep(POLL_INTERVAL)
        continue

    status_col  = row.get("processing_status") or ""
    ocr_done    = bool(row.get("ocr_text"))
    error_val   = row.get("processing_error")

    # ── check for failure ──────────────────────────────────────────────────
    if status_col == "failed" or error_val:
        err(f"Pipeline FAILED: {error_val or 'unknown error'}")
        sys.exit(1)

    # ── count lab_results once OCR is done ─────────────────────────────────
    lab_count = 0
    if ocr_done or status_col in ("ocr_complete", "done"):
        try:
            lab_count = len(
                (client.table("lab_results")
                 .select("id")
                 .eq("report_id", report_id)
                 .execute()
                ).data or []
            )
        except Exception:
            pass

    # ── decide stage ───────────────────────────────────────────────────────
    if status_col == "done" or (ocr_done and lab_count > 0):
        ok(f"[{elapsed:>5.0f}s] Pipeline complete! ({lab_count} lab results)")
        break
    elif status_col == "ocr_complete" or (ocr_done and lab_count == 0):
        print(f"  [{elapsed:>5.0f}s] {Y}OCR done{X}, Gemini extracting…")
    else:
        print(f"  [{elapsed:>5.0f}s] {D}OCR running…{X}")

    time.sleep(POLL_INTERVAL)
else:
    err(f"Timed out after {MAX_WAIT}s — pipeline did not complete")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — print extracted lab results
# ══════════════════════════════════════════════════════════════════════════════
banner("Step 4 — Extracted lab results")

labs = (
    client.table("lab_results")
    .select("test_name, value, unit, reference_range, abnormal_flag")
    .eq("report_id", report_id)
    .order("test_name")
    .execute()
).data or []

if not labs:
    info("No lab results found.")
else:
    ok(f"{len(labs)} lab result(s):")
    print()
    hdr = f"  {'#':>3}  {'Test Name':<38} {'Value':>10} {'Unit':<18} {'Abnormal':>9}"
    sep = "  " + "─" * 82
    print(f"{B}{hdr}{X}")
    print(sep)
    for i, lab in enumerate(labs, 1):
        val  = str(lab.get("value", "—")) if lab.get("value") is not None else "—"
        unit = lab.get("unit") or "—"
        abn  = lab.get("abnormal_flag")
        abn_s = f"{R}YES{X}" if abn else (f"{D}no{X}" if abn is False else "—")
        name  = (lab.get("test_name") or "")[:38]
        print(f"  {i:>3}  {name:<38} {val:>10} {unit:<18} {abn_s}")
    print(sep)

print()
ok("All done ✓")
print()
