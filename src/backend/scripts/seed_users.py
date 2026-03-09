"""Seed script — creates 3 synthetic users and runs the full pipeline.

Uploads sample PDFs from ``src/sample_reports/``, runs OCR → Gemini
extraction → alerts evaluation for each user, and prints a coloured
summary at the end.

Usage (from the ``src/`` directory):
    PYTHONPATH=. python backend/scripts/seed_users.py

Environment:
    Reads ``backend/.env`` automatically (same as the live server).

Users created
-------------
  Arjun Sharma   (5 reports) — diabetes, high_cholesterol, hypothyroidism,
                               cardiac_risk, ckd_early
  Priya Nair     (4 reports) — iron_deficiency, anaemia_b12,
                               vit_d_deficiency, pcos
  Vikram Reddy   (3 reports) — metabolic_syndrome, multi_condition, healthy

Each user is assigned a **fixed UUID** so the script is safe to re-run
(Supabase storage ``upsert=False`` will reject duplicate uploads, which is
caught and skipped gracefully).
"""

from __future__ import annotations

import os
import sys
import time
import traceback
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap — make sure we can import backend.*
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent          # backend/scripts/
_SRC_DIR    = _SCRIPT_DIR.parents[1]                   # src/
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Load .env before any backend imports so supabase_client picks up the vars.
from dotenv import load_dotenv
load_dotenv(_SCRIPT_DIR.parent / ".env")               # backend/.env

# ---------------------------------------------------------------------------
# Coloured output helpers
# ---------------------------------------------------------------------------
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_RED    = "\033[91m"
_GREEN  = "\033[92m"
_YELLOW = "\033[93m"
_CYAN   = "\033[96m"
_DIM    = "\033[2m"
_BLUE   = "\033[94m"
_MAG    = "\033[95m"

def banner(text: str) -> None:
    width = 66
    print()
    print(f"{_BOLD}{_BLUE}{'━' * width}{_RESET}")
    print(f"{_BOLD}{_BLUE}  {text}{_RESET}")
    print(f"{_BOLD}{_BLUE}{'━' * width}{_RESET}")

def sub_banner(text: str) -> None:
    print(f"\n{_BOLD}{_CYAN}  ▶  {text}{_RESET}")

def ok(text: str)   -> None: print(f"  {_GREEN}✔{_RESET}  {text}")
def err(text: str)  -> None: print(f"  {_RED}✘{_RESET}  {text}")
def info(text: str) -> None: print(f"  {_YELLOW}ℹ{_RESET}  {text}")
def dim(text: str)  -> None: print(f"  {_DIM}{text}{_RESET}")

# ---------------------------------------------------------------------------
# Backend imports (after path + dotenv setup)
# ---------------------------------------------------------------------------
from backend.config.supabase_client import (
    get_supabase_client,
    get_reports_bucket,
    get_ocr_reports_table,
)
from backend.controllers.reports_controller import (
    upload_medical_report,
    run_ocr_on_report,
    extract_labs_with_gemini,
    ReportUploadError,
    ReportOCRError,
)

# ---------------------------------------------------------------------------
# User definitions
# ---------------------------------------------------------------------------
# Fixed UUIDs make the script idempotent across runs.
_SAMPLE_DIR = _SRC_DIR / "sample_reports"

# Set True to wipe all previous data for the 3 seed users before re-seeding.
# This ensures storage folders are named correctly (Name_uuid/) on every run.
CLEAN_BEFORE_SEED = True

USERS: list[dict] = [
    {
        "name":    "Arjun Sharma",
        "user_id": "aaaaaaaa-0001-0001-0001-000000000001",
        "reports": [
            ("diabetes",         "diabetes/diabetes__Ramesh_Kumar__52M.pdf"),
            ("high_cholesterol", "high_cholesterol/high_cholesterol__Kiran_Mehta__40M.pdf"),
            ("hypothyroidism",   "hypothyroidism/hypothyroidism__Arvind_Pillai__38M.pdf"),
            ("cardiac_risk",     "cardiac_risk/cardiac_risk__Vijay_Anand__58M.pdf"),
            ("ckd_early",        "ckd_early/ckd_early__Venkatesh_Rao__65M.pdf"),
        ],
    },
    {
        "name":    "Priya Nair",
        "user_id": "bbbbbbbb-0002-0002-0002-000000000002",
        "reports": [
            ("iron_deficiency",  "iron_deficiency/iron_deficiency__Riya_Sharma__28F.pdf"),
            ("anaemia_b12",      "anaemia_b12/anaemia_b12__Revathi_Menon__29F.pdf"),
            ("vit_d_deficiency", "vit_d_deficiency/vit_d_deficiency__Aishwarya_Patel__26F.pdf"),
            ("pcos",             "pcos/pcos__Swathi_Reddy__24F.pdf"),
        ],
    },
    {
        "name":    "Vikram Reddy",
        "user_id": "cccccccc-0003-0003-0003-000000000003",
        "reports": [
            ("metabolic_syndrome", "metabolic_syndrome/metabolic_syndrome__Dinesh_Pandey__48M.pdf"),
            ("multi_condition",    "multi_condition/multi_condition__Ajith_Kumar__55M.pdf"),
            ("healthy",            "healthy/healthy__Aarav_Gupta__24M.pdf"),
        ],
    },
]

# ---------------------------------------------------------------------------
# Cleanup — wipe previous seed data for one user
# ---------------------------------------------------------------------------

def cleanup_user(client, bucket: str, table: str, user_id: str, name: str) -> None:
    """Delete all storage files, DB rows, and alerts for a seed user.

    Makes the script fully idempotent: running it twice produces exactly one
    clean set of named folders instead of accumulating duplicates.
    """
    sub_banner(f"Cleaning up previous data for {name} …")

    # 1. Find all existing medical_reports rows for this user.
    try:
        rows = (
            client.table(table)
            .select("id, source_url")
            .eq("user_id", user_id)
            .execute()
        ).data or []
    except Exception as exc:
        info(f"Could not query existing reports (skipping cleanup): {exc}")
        return

    if not rows:
        info("No previous data found — nothing to clean.")
        return

    report_ids = [r["id"] for r in rows]

    # 2. Delete storage files.
    #    Derive the storage path from source_url: everything after "/object/public/<bucket>/"
    storage_paths: list[str] = []
    for r in rows:
        url = r.get("source_url") or ""
        marker = f"/object/public/{bucket}/"
        if marker in url:
            storage_paths.append(url.split(marker, 1)[1])

    if storage_paths:
        try:
            client.storage.from_(bucket).remove(storage_paths)
            ok(f"Deleted {len(storage_paths)} file(s) from storage")
        except Exception as exc:
            info(f"Storage delete partial/failed (continuing): {exc}")
    else:
        info("No storage paths found to delete")

    # 3. Delete lab_results rows.
    try:
        client.table("lab_results").delete().in_("report_id", report_ids).execute()
        ok(f"Deleted lab_results for {len(report_ids)} report(s)")
    except Exception as exc:
        info(f"lab_results delete failed (continuing): {exc}")

    # 4. Delete alert_evidence + alerts.
    try:
        alert_rows = (
            client.table("alerts")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        ).data or []
        alert_ids = [a["id"] for a in alert_rows]
        if alert_ids:
            client.table("alert_evidence").delete().in_("alert_id", alert_ids).execute()
        client.table("alerts").delete().eq("user_id", user_id).execute()
        ok(f"Deleted {len(alert_ids)} alert(s) and their evidence")
    except Exception as exc:
        info(f"Alerts delete failed (continuing): {exc}")

    # 5. Delete medical_reports rows.
    try:
        client.table(table).delete().eq("user_id", user_id).execute()
        ok(f"Deleted {len(report_ids)} medical_reports row(s)")
    except Exception as exc:
        info(f"medical_reports delete failed (continuing): {exc}")


# ---------------------------------------------------------------------------
# Per-report pipeline
# ---------------------------------------------------------------------------

def _process_report(
    client,
    bucket: str,
    table: str,
    user_id: str,
    first: str,
    last: str,
    condition: str,
    rel_path: str,
    report_num: int,
) -> dict:
    """Upload one PDF and run the full OCR→Gemini pipeline.

    Uses ``upload_medical_report`` → ``run_ocr_on_report`` → ``extract_labs_with_gemini``.
    Does NOT require the processing_status migration (003) to be applied.

    Returns a result dict with keys: ``report_id``, ``status``, ``error``.
    """
    pdf_path = _SAMPLE_DIR / rel_path
    upload_name = f"{condition}_{first}_{last}_report{report_num}.pdf"

    dim(f"  Source : {rel_path}")
    dim(f"  Upload : {upload_name}")

    if not pdf_path.exists():
        msg = f"PDF not found: {pdf_path}"
        err(msg)
        return {"report_id": None, "status": "skipped", "error": msg}

    file_bytes = pdf_path.read_bytes()

    # ── Stage 1: upload to Supabase Storage ──────────────────────────────
    try:
        storage_path, public_url = upload_medical_report(
            client, bucket, user_id, upload_name, file_bytes, "application/pdf",
            user_name=f"{first} {last}",
        )
        ok(f"Uploaded  →  {storage_path}")
    except ReportUploadError as exc:
        exc_str = str(exc)
        if any(k in exc_str.lower() for k in ("already exists", "duplicate", "violates")):
            info(f"Storage file already exists — skipping (already seeded): {upload_name}")
            return {"report_id": None, "status": "skipped",
                    "error": "duplicate upload (already seeded)"}
        err(f"Upload failed: {exc}")
        return {"report_id": None, "status": "failed", "error": exc_str}
    except Exception as exc:
        err(f"Unexpected upload error: {exc}")
        return {"report_id": None, "status": "failed", "error": str(exc)}

    # ── Stage 2: OCR + DB insert + RAG indexing ───────────────────────────
    info("Running OCR (Tesseract) — this may take 15–45 s …")
    t0 = time.time()
    try:
        _ocr_text, confidence, report_id = run_ocr_on_report(
            client, bucket, table, user_id, storage_path
        )
        elapsed = time.time() - t0
        ok(f"OCR complete  ({elapsed:.1f} s, conf={confidence:.1f}%)  →  report_id={report_id}")
    except ReportOCRError as exc:
        elapsed = time.time() - t0
        err(f"OCR failed after {elapsed:.1f} s: {exc}")
        return {"report_id": None, "status": "failed", "error": str(exc)}
    except Exception as exc:
        elapsed = time.time() - t0
        err(f"Unexpected OCR error after {elapsed:.1f} s: {exc}")
        traceback.print_exc()
        return {"report_id": None, "status": "failed", "error": str(exc)}

    # ── Stage 3: Gemini lab extraction ────────────────────────────────────
    info("Running Gemini extraction …")
    t1 = time.time()
    try:
        extract_labs_with_gemini(client, report_id)
        elapsed = time.time() - t1
        ok(f"Gemini extraction complete  ({elapsed:.1f} s)")
        return {"report_id": report_id, "status": "done", "error": None}
    except Exception as exc:
        elapsed = time.time() - t1
        err(f"Gemini extraction failed after {elapsed:.1f} s: {exc}")
        traceback.print_exc()
        # OCR succeeded so we still count this as partial — report row exists.
        return {"report_id": report_id, "status": "failed", "error": str(exc)}


# ---------------------------------------------------------------------------
# Alerts evaluation (post-pipeline, per user)
# ---------------------------------------------------------------------------

def _run_alerts(client, user_id: str, user_name: str) -> dict:
    """Evaluate rules + persist alerts for one user."""
    sub_banner(f"Evaluating alerts for {user_name} …")
    try:
        from backend.rules.engine import evaluate_rules
        from backend.rules.inserter import persist_alerts
    except ImportError as exc:
        err(f"Rules engine not importable: {exc}")
        return {"alerts_triggered": 0, "error": str(exc)}

    try:
        alerts = evaluate_rules(client=client, user_id=user_id)
        ok(f"Rules evaluated — {len(alerts)} alert(s) triggered")
    except Exception as exc:
        err(f"evaluate_rules() failed: {exc}")
        traceback.print_exc()
        return {"alerts_triggered": 0, "error": str(exc)}

    try:
        result = persist_alerts(client=client, user_id=user_id, alerts=alerts)
        ok(
            f"Alerts persisted — inserted={result.get('inserted', '?')}, "
            f"evidence_inserted={result.get('evidence_inserted', '?')}"
        )
        return {
            "alerts_triggered": len(alerts),
            "inserted":         result.get("inserted", 0),
            "evidence_inserted": result.get("evidence_inserted", 0),
            "errors":            result.get("errors", []),
        }
    except Exception as exc:
        err(f"persist_alerts() failed: {exc}")
        traceback.print_exc()
        return {"alerts_triggered": len(alerts), "error": str(exc)}


# ---------------------------------------------------------------------------
# Final summary table
# ---------------------------------------------------------------------------

def _print_summary(summary: list[dict]) -> None:
    banner("SEED SUMMARY")
    col_w = [22, 10, 10, 10, 12, 10]
    headers = ["User", "Reports", "Done", "Failed", "Alerts", "Evidence"]

    def _row(cells: list, bold: bool = False) -> str:
        parts = []
        for i, c in enumerate(cells):
            parts.append(str(c).ljust(col_w[i]))
        line = "  ".join(parts)
        return (f"{_BOLD}{line}{_RESET}" if bold else f"  {line}")

    print(_row(headers, bold=True))
    print(f"  {'─' * sum(col_w + [2 * (len(col_w) - 1)])}")
    for row in summary:
        status_color = _GREEN if row["failed"] == 0 else _YELLOW
        cells = [
            row["name"],
            row["reports"],
            f"{_GREEN}{row['done']}{_RESET}",
            f"{_RED if row['failed'] else _DIM}{row['failed']}{_RESET}",
            f"{status_color}{row['alerts']}{_RESET}",
            f"{_DIM}{row['evidence']}{_RESET}",
        ]
        # Build plain row then inject colour codes
        plain = [row["name"], row["reports"], row["done"], row["failed"], row["alerts"], row["evidence"]]
        print(_row([str(p) for p in plain]))
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    banner("VITALIS — User Seed Script")
    print(f"  Sample reports dir : {_SAMPLE_DIR}")
    print(f"  Users to seed      : {len(USERS)}")
    print(f"  Total reports      : {sum(len(u['reports']) for u in USERS)}")

    client = get_supabase_client()
    bucket = get_reports_bucket()
    table  = get_ocr_reports_table()

    info(f"Supabase bucket : {bucket}")
    info(f"DB table        : {table}")

    summary: list[dict] = []

    for user in USERS:
        name    = user["name"]
        user_id = user["user_id"]
        reports = user["reports"]
        first, last = name.split(maxsplit=1)

        banner(f"USER: {name}  ({len(reports)} reports)  id={user_id}")

        if CLEAN_BEFORE_SEED:
            cleanup_user(client, bucket, table, user_id, name)

        user_stats = {
            "name": name,
            "reports": len(reports),
            "done": 0,
            "failed": 0,
            "skipped": 0,
            "alerts": 0,
            "evidence": 0,
        }

        for n, (condition, rel_path) in enumerate(reports, start=1):
            sub_banner(f"Report {n}/{len(reports)}  —  {condition}")
            result = _process_report(
                client, bucket, table,
                user_id, first, last,
                condition, rel_path, n
            )
            if result["status"] == "done":
                user_stats["done"] += 1
            elif result["status"] == "skipped":
                user_stats["skipped"] += 1
            else:
                user_stats["failed"] += 1

        # Run alerts only if at least one report was successfully processed.
        if user_stats["done"] > 0:
            alerts_result = _run_alerts(client, user_id, name)
            user_stats["alerts"]   = alerts_result.get("alerts_triggered", 0)
            user_stats["evidence"] = alerts_result.get("evidence_inserted", 0)
        else:
            info("No successful reports — skipping alerts evaluation.")

        summary.append(user_stats)
        ok(
            f"User {name} done — "
            f"reports={user_stats['done']} ok / {user_stats['failed']} failed, "
            f"alerts={user_stats['alerts']}"
        )

    _print_summary(summary)

    total_done   = sum(u["done"] for u in summary)
    total_failed = sum(u["failed"] for u in summary)
    total_alerts = sum(u["alerts"] for u in summary)
    print(
        f"{_BOLD}Totals:{_RESET}  "
        f"{_GREEN}{total_done} reports processed{_RESET},  "
        f"{_RED if total_failed else _DIM}{total_failed} failed{_RESET},  "
        f"{_CYAN}{total_alerts} alerts generated{_RESET}"
    )
    print()


if __name__ == "__main__":
    main()
