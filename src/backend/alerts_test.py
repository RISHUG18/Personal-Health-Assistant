#!/usr/bin/env python3
"""Standalone alerts / rules engine test.

Two modes in one script
───────────────────────
PART A — Unit tests (no DB, no API key required)
    Runs all 13 rule functions against hand-crafted LabRow fixtures.
    Tests both the "should fire" and "should NOT fire" branches.
    Verifies severity escalation (e.g. critically low Hb → HIGH, mildly
    low → MEDIUM) and confirms that rules are pure and isolated.

PART B — Integration test (requires Supabase + real lab data)
    1. Reads every lab_results row for TEST_USER_ID from Supabase.
    2. Evaluates all 13 rules against that real data.
    3. Shows a detailed per-rule report (triggered / not triggered).
    4. Persists alerts + evidence to Supabase (idempotent).
    5. Re-queries Supabase and prints the final stored alerts with evidence.

──────────────────────────────────────────────────────────────────────
CONFIGURATION — edit the variable below, then run:

    cd src
    PYTHONPATH=. python backend/alerts_test.py
──────────────────────────────────────────────────────────────────────
"""

import os
import sys
import time
import uuid

# ── ▼▼▼  CONFIGURE HERE  ▼▼▼ ──────────────────────────────────────────────────

# Must match a user_id that already has medical_reports + lab_results in DB.
# (Use TEST_USER_ID from cleaning_pipeline_test.py if you ran that first.)
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"

# Set False to skip Part B (DB integration) and only run unit tests.
RUN_INTEGRATION = True

# ── ▲▲▲  END CONFIG  ▲▲▲ ──────────────────────────────────────────────────────

_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from backend.rules.definitions import ALL_RULES, LabRow
from backend.rules.models import AlertRecord, Severity

# ── Terminal colours ───────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
MAGENTA = "\033[95m"
RESET  = "\033[0m"

def banner(title: str) -> None:
    w = 72
    print(f"\n{CYAN}{BOLD}{'═' * w}")
    print(f"  {title}")
    print(f"{'═' * w}{RESET}\n")

def sub_banner(title: str) -> None:
    print(f"\n{MAGENTA}{BOLD}  ── {title} {('─' * max(0, 66 - len(title)))}{RESET}\n")

def ok(msg: str)   -> None: print(f"  {GREEN}✅  {msg}{RESET}")
def err(msg: str)  -> None: print(f"  {RED}❌  {msg}{RESET}")
def info(msg: str) -> None: print(f"  {YELLOW}ℹ   {msg}{RESET}")
def dim(msg: str)  -> None: print(f"  {DIM}{msg}{RESET}")


# ── Helper: build a LabRow quickly ────────────────────────────────────────────

def _row(
    name: str,
    value: float | None,
    unit: str = "mg/dL",
    abnormal: bool | None = None,
    ref: str | None = None,
    report_id: str | None = None,
) -> LabRow:
    return LabRow(
        lab_result_id=str(uuid.uuid4()),
        report_id=report_id or str(uuid.uuid4()),
        test_name=name,
        value=value,
        unit=unit,
        reference_range=ref,
        abnormal_flag=abnormal,
        report_date="2026-01-01",
        ocr_snippet=f"{name}  {value}  {unit}",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PART A — UNIT TESTS (pure, no DB)
# ═══════════════════════════════════════════════════════════════════════════════

# Each tuple: (rows, rule_id, expected_triggered, expected_severity_or_None)
_UNIT_CASES: list[tuple] = [
    # ── any_abnormal ──────────────────────────────────────────────────────────
    ([_row("Hemoglobin", 14, abnormal=True),
      _row("WBC", 7, abnormal=False)],
     "any_abnormal", True,  Severity.MEDIUM),   # 1 abnormal → MEDIUM

    ([_row("Hemoglobin", 14, abnormal=True),
      _row("WBC", 3, abnormal=True),
      _row("Platelet Count", 90, abnormal=True)],
     "any_abnormal", True,  Severity.HIGH),     # 3 abnormal → HIGH

    ([_row("Hemoglobin", 14, abnormal=False)],
     "any_abnormal", False, None),              # no abnormal flags

    # ── low_hemoglobin ────────────────────────────────────────────────────────
    ([_row("Hemoglobin", 7.0, "g/dL")],
     "low_hemoglobin", True, Severity.HIGH),    # < 8 → HIGH

    ([_row("Hemoglobin", 10.5, "g/dL")],
     "low_hemoglobin", True, Severity.MEDIUM),  # 8–12 → MEDIUM

    ([_row("Hemoglobin", 13.5, "g/dL")],
     "low_hemoglobin", False, None),            # normal

    ([_row("Haemoglobin", 9.0, "g/dL")],
     "low_hemoglobin", True, Severity.MEDIUM),  # alternate spelling

    # ── high_cholesterol ──────────────────────────────────────────────────────
    ([_row("Total Cholesterol", 260)],
     "high_cholesterol", True, Severity.HIGH),  # > 240

    ([_row("Cholesterol", 215)],
     "high_cholesterol", True, Severity.LOW),   # 200–240

    ([_row("Total Cholesterol", 185)],
     "high_cholesterol", False, None),          # normal

    ([_row("HDL Cholesterol", 260)],            # HDL excluded from rule
     "high_cholesterol", False, None),

    # ── high_ldl ─────────────────────────────────────────────────────────────
    ([_row("LDL Cholesterol", 200)],
     "high_ldl", True,  Severity.HIGH),         # > 190

    ([_row("LDL", 170)],
     "high_ldl", True,  Severity.MEDIUM),       # 160–190

    ([_row("LDL", 130)],
     "high_ldl", False, None),                  # normal

    # ── high_blood_sugar ──────────────────────────────────────────────────────
    ([_row("Fasting Blood Glucose", 135)],
     "high_blood_sugar", True,  Severity.HIGH),  # > 126

    ([_row("FBS", 110)],
     "high_blood_sugar", True,  Severity.MEDIUM), # 100–126

    ([_row("Blood Glucose", 90)],
     "high_blood_sugar", False, None),            # normal

    # ── high_hba1c ────────────────────────────────────────────────────────────
    ([_row("HbA1c", 7.5, "%")],
     "high_hba1c", True,  Severity.HIGH),        # ≥ 6.5

    ([_row("HBA1C", 6.0, "%")],
     "high_hba1c", True,  Severity.MEDIUM),      # 5.7–6.5

    ([_row("Glycated Hemoglobin", 5.5, "%")],
     "high_hba1c", False, None),                 # normal

    # ── abnormal_tsh ──────────────────────────────────────────────────────────
    ([_row("TSH", 12.0, "µIU/mL")],
     "abnormal_tsh", True,  Severity.HIGH),      # > 10

    ([_row("Thyroid Stimulating Hormone", 5.5, "µIU/mL")],
     "abnormal_tsh", True,  Severity.MEDIUM),    # 4.5–10 (high)

    ([_row("TSH", 0.2, "µIU/mL")],
     "abnormal_tsh", True,  Severity.MEDIUM),    # < 0.4 (low/hyper)

    ([_row("TSH", 2.5, "µIU/mL")],
     "abnormal_tsh", False, None),               # normal 0.4–4.5

    # ── low_vitamin_d ─────────────────────────────────────────────────────────
    ([_row("Vitamin D 25-OH", 8.0, "ng/mL")],
     "low_vitamin_d", True,  Severity.HIGH),     # < 12

    ([_row("Vit D", 22.0, "ng/mL")],
     "low_vitamin_d", True,  Severity.MEDIUM),   # 12–30

    ([_row("25(OH) Vitamin D", 45.0, "ng/mL")],
     "low_vitamin_d", False, None),              # normal

    # ── low_b12 ───────────────────────────────────────────────────────────────
    ([_row("Vitamin B12", 120.0, "pg/mL")],
     "low_b12", True,  Severity.HIGH),           # < 150

    ([_row("Cyanocobalamin", 200.0, "pg/mL")],
     "low_b12", True,  Severity.MEDIUM),         # 150–300

    ([_row("Vitamin B12", 450.0, "pg/mL")],
     "low_b12", False, None),                    # normal

    # ── high_creatinine ───────────────────────────────────────────────────────
    ([_row("Serum Creatinine", 2.5)],
     "high_creatinine", True,  Severity.HIGH),   # > 2.0

    ([_row("Creatinine", 1.6)],
     "high_creatinine", True,  Severity.MEDIUM), # 1.3–2.0

    ([_row("Creatinine", 0.9)],
     "high_creatinine", False, None),            # normal

    ([_row("Urine Creatinine", 2.8)],            # urine excluded
     "high_creatinine", False, None),

    # ── low_platelets ─────────────────────────────────────────────────────────
    ([_row("Platelet Count", 40.0, "x10^3/uL")],
     "low_platelets", True,  Severity.HIGH),     # < 50

    ([_row("PLT", 120.0, "x10^3/uL")],
     "low_platelets", True,  Severity.MEDIUM),   # 50–150

    ([_row("Platelet Count", 200.0, "x10^3/uL")],
     "low_platelets", False, None),              # normal

    # ── abnormal_wbc ──────────────────────────────────────────────────────────
    ([_row("WBC", 17.0, "x10^3/uL")],
     "abnormal_wbc", True,  Severity.HIGH),      # > 15

    ([_row("Total Leucocyte Count", 1.5, "x10^3/uL")],
     "abnormal_wbc", True,  Severity.HIGH),      # < 2

    ([_row("TLC", 13.0, "x10^3/uL")],
     "abnormal_wbc", True,  Severity.MEDIUM),    # 11–15

    ([_row("WBC", 7.0, "x10^3/uL")],
     "abnormal_wbc", False, None),               # normal

    # ── missing_critical_tests ────────────────────────────────────────────────
    ([],                                          # no rows at all
     "missing_critical_tests", True,  Severity.LOW),

    ([_row("Hemoglobin", 14, "g/dL"),
      _row("WBC", 7),
      _row("Blood Glucose", 90)],
     "missing_critical_tests", False, None),     # both CBC + metabolic present
]


def run_unit_tests() -> tuple[int, int]:
    """Run all unit test cases. Returns (passed, failed)."""
    banner("PART A — UNIT TESTS  (no DB required)")

    rule_map = {r.rule_id: r for r in ALL_RULES}
    passed = failed = 0

    # Column header
    hdr = (f"  {'#':>3}  {'Rule ID':<28} {'Input rows':<30} "
           f"{'Expected':>10} {'Got':>10} {'Severity':<10}")
    sep = "  " + "─" * 98
    print(hdr)
    print(sep)

    for i, (rows, rule_id, expected_triggered, expected_severity) in enumerate(_UNIT_CASES, 1):
        rule = rule_map[rule_id]
        result = rule.func("unit-test-user", rows)

        triggered_ok  = result.triggered == expected_triggered
        severity_ok   = (
            expected_severity is None or
            not expected_triggered or
            result.severity == expected_severity
        )
        overall_ok = triggered_ok and severity_ok

        status = f"{GREEN}PASS{RESET}" if overall_ok else f"{RED}FAIL{RESET}"
        exp    = "FIRE  " if expected_triggered else "skip  "
        got    = "FIRE  " if result.triggered   else "skip  "
        sev    = result.severity.value if result.severity else "—"

        # Short row description
        if rows:
            row_desc = f"{rows[0].test_name[:22]}={rows[0].value}"
            if len(rows) > 1:
                row_desc += f" +{len(rows)-1}"
        else:
            row_desc = "(no rows)"

        print(f"  [{status}] {i:>3}  {rule_id:<28} {row_desc:<30} "
              f"{exp:>10} {got:>10} {sev:<10}")

        if not overall_ok:
            if not triggered_ok:
                print(f"        {RED}→ triggered mismatch: expected {expected_triggered}, "
                      f"got {result.triggered}{RESET}")
            if not severity_ok:
                print(f"        {RED}→ severity mismatch: expected {expected_severity}, "
                      f"got {result.severity}{RESET}")
            if result.reason:
                print(f"        reason: {result.reason}")
            failed += 1
        else:
            passed += 1

        if result.triggered and result.reason and not overall_ok:
            print(f"        {DIM}reason: {result.reason}{RESET}")

    print(sep)
    print()
    total = passed + failed
    if failed == 0:
        ok(f"ALL {passed}/{total} UNIT TESTS PASSED")
    else:
        err(f"{failed}/{total} tests FAILED — see above")
        ok(f"{passed}/{total} tests passed")

    return passed, failed


# ═══════════════════════════════════════════════════════════════════════════════
# PART B — INTEGRATION TEST (real Supabase data)
# ═══════════════════════════════════════════════════════════════════════════════


def step_fetch_lab_data(db, user_id: str) -> tuple[list[dict], list[dict]]:
    """Fetch medical_reports + lab_results from Supabase and print summary."""
    sub_banner("Step B1 — Fetch lab data from Supabase")

    # Reports
    reports_resp = (
        db.table("medical_reports")
        .select("id, report_date, report_type, source_file_name, ocr_confidence")
        .eq("user_id", user_id)
        .execute()
    )
    reports = reports_resp.data or []

    if not reports:
        err(f"No medical_reports found for user_id={user_id}")
        info("Run cleaning_pipeline_test.py first to populate data.")
        return [], []

    ok(f"Found {len(reports)} report(s) for user_id={user_id}")
    for r in reports:
        info(f"  report_id={r['id'][:8]}…  "
             f"date={r.get('report_date') or '—'}  "
             f"type={r.get('report_type') or '—'}  "
             f"file={r.get('source_file_name') or '—'}  "
             f"confidence={r.get('ocr_confidence') or '—'}")

    # Lab results
    report_ids = [r["id"] for r in reports]
    labs_resp = (
        db.table("lab_results")
        .select("id, report_id, test_name, value, unit, reference_range, abnormal_flag, extracted_from_page")
        .in_("report_id", report_ids)
        .execute()
    )
    labs = labs_resp.data or []

    print()
    if not labs:
        err("No lab_results found — run cleaning_pipeline_test.py first.")
        return reports, []

    ok(f"Found {len(labs)} lab_results row(s) across all reports:")
    hdr = f"  {'#':>3}  {'Test Name':<38} {'Value':>10} {'Unit':<18} {'Ref Range':<25} {'Abn':>5}"
    sep = "  " + "─" * 104
    print(hdr)
    print(sep)
    for i, lab in enumerate(labs, 1):
        val    = str(lab.get("value")) if lab.get("value") is not None else "—"
        unit   = lab.get("unit") or "—"
        ref    = lab.get("reference_range") or "—"
        abn    = lab.get("abnormal_flag")
        abn_s  = "YES" if abn is True else ("no" if abn is False else "—")
        colour = RED if abn is True else ""
        reset  = RESET if abn is True else ""
        print(f"  {colour}{i:>3}  {lab['test_name']:<38} {val:>10} {unit:<18} {ref:<25} {abn_s:>5}{reset}")
    print(sep)

    return reports, labs


def step_evaluate_rules(db, user_id: str) -> list[AlertRecord]:
    """Run the rules engine and print a per-rule breakdown."""
    sub_banner("Step B2 — Evaluate all 13 rules")

    from backend.rules.engine import evaluate_rules

    t0 = time.time()
    alerts = evaluate_rules(client=db, user_id=user_id)
    elapsed = time.time() - t0

    # ── Per-rule report ───────────────────────────────────────────────────────
    # We need the individual RuleResults for the detailed display.
    # Re-run rule functions directly against the fetched LabRows (already
    # fetched inside evaluate_rules; we replicate the fetch here just for display).
    from backend.rules.engine import _fetch_reports, _fetch_lab_results, _build_lab_rows

    report_map  = _fetch_reports(db, user_id)
    raw_labs    = _fetch_lab_results(db, list(report_map.keys()))
    lab_rows    = _build_lab_rows(report_map, raw_labs)

    print(f"  Rules evaluated against {len(lab_rows)} lab rows in {elapsed:.2f}s\n")

    hdr = f"  {'Rule ID':<30} {'Status':<10} {'Severity':<10} Reason"
    sep = "  " + "─" * 110
    print(hdr)
    print(sep)

    alert_map = {a.reason: a for a in alerts}

    for rule_def in ALL_RULES:
        result = rule_def.func(user_id, lab_rows)
        if result.triggered:
            sev_colour = RED if result.severity == Severity.HIGH else YELLOW
            status     = f"{sev_colour}TRIGGERED{RESET}"
            sev_str    = f"{sev_colour}{result.severity.value.upper()}{RESET}"
            reason_short = (result.reason or "")[:65]
            if len(result.reason or "") > 65:
                reason_short += "…"
        else:
            status  = f"{DIM}–{RESET}"
            sev_str = f"{DIM}—{RESET}"
            reason_short = f"{DIM}not triggered{RESET}"

        print(f"  {rule_def.rule_id:<30} {status:<20} {sev_str:<20} {reason_short}")

    print(sep)
    print()
    ok(f"{len(alerts)}/{len(ALL_RULES)} rules triggered  ({elapsed:.2f}s)")
    return alerts


def step_persist_alerts(db, user_id: str, alerts: list[AlertRecord]) -> dict:
    """Persist alerts to Supabase and print the insert summary."""
    sub_banner("Step B3 — Persist alerts to Supabase")

    from backend.rules.inserter import persist_alerts

    result = persist_alerts(client=db, user_id=user_id, alerts=alerts)

    if result["errors"]:
        for e in result["errors"]:
            err(f"DB error: {e}")
    else:
        ok("No DB errors during persistence")

    ok(f"Old alerts deleted  : {result['deleted']}")
    ok(f"New alerts inserted : {result['inserted']}")
    ok(f"Evidence rows       : {result['evidence_inserted']}")

    return result


def step_verify_alerts(db, user_id: str) -> None:
    """Query Supabase and print the final stored alerts with evidence."""
    sub_banner("Step B4 — Verify stored alerts (query Supabase)")

    # Fetch alerts
    alert_rows = (
        db.table("alerts")
        .select("id, severity, reason, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    ).data or []

    if not alert_rows:
        err("No alerts found in DB — something went wrong in the persist step.")
        return

    ok(f"{len(alert_rows)} alert(s) stored in Supabase:\n")

    for i, alert in enumerate(alert_rows, 1):
        sev = alert["severity"]
        sev_colour = RED if sev == "high" else (YELLOW if sev == "medium" else DIM)
        sev_label  = f"{sev_colour}[{sev.upper():^6}]{RESET}"

        print(f"  {i:>2}. {sev_label}  {alert['reason']}")
        print(f"       {DIM}alert_id  : {alert['id']}{RESET}")
        print(f"       {DIM}created_at: {alert['created_at']}{RESET}")

        # Fetch evidence for this alert
        ev_rows = (
            db.table("alert_evidence")
            .select("lab_result_id, report_id, ocr_text_snippet")
            .eq("alert_id", alert["id"])
            .execute()
        ).data or []

        if ev_rows:
            for ev in ev_rows:
                lab_id  = (ev.get("lab_result_id") or "")[:8]
                rep_id  = (ev.get("report_id") or "")[:8]
                snippet = ev.get("ocr_text_snippet") or "—"
                print(f"       {DIM}evidence  : lab_result={lab_id}… "
                      f"report={rep_id}… snippet='{snippet[:60]}'{RESET}")
        else:
            print(f"       {DIM}evidence  : (none — data_quality rule or no direct row link){RESET}")

        print()

    # Severity breakdown
    from collections import Counter
    counts = Counter(a["severity"] for a in alert_rows)
    print(f"  Severity summary:  "
          f"{RED}HIGH={counts.get('high', 0)}{RESET}  "
          f"{YELLOW}MEDIUM={counts.get('medium', 0)}{RESET}  "
          f"LOW={counts.get('low', 0)}")


def run_integration_test(db) -> None:
    """Run the full DB integration test."""
    banner(f"PART B — INTEGRATION TEST  (user_id={TEST_USER_ID[:8]}…)")
    info(f"User ID : {TEST_USER_ID}")

    t0 = time.time()

    # B1 — Fetch
    reports, labs = step_fetch_lab_data(db, TEST_USER_ID)
    if not labs:
        err("Skipping evaluation — no lab data available.")
        return

    # B2 — Evaluate
    alerts = step_evaluate_rules(db, TEST_USER_ID)

    # B3 — Persist
    step_persist_alerts(db, TEST_USER_ID, alerts)

    # B4 — Verify
    step_verify_alerts(db, TEST_USER_ID)

    print()
    ok(f"Integration test complete in {time.time() - t0:.1f}s")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    banner("ALERTS ENGINE TEST")

    # ── PART A: Unit tests (always run) ──────────────────────────────────────
    unit_passed, unit_failed = run_unit_tests()

    # ── PART B: Integration test ──────────────────────────────────────────────
    if not RUN_INTEGRATION:
        info("RUN_INTEGRATION=False — skipping DB integration test.")
        print()
        return

    supa_url = os.getenv("SUPABASE_URL")
    supa_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supa_url or not supa_key:
        err("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set in src/backend/.env")
        info("Set RUN_INTEGRATION=False to run unit tests only.")
        sys.exit(1)

    from supabase import create_client
    db = create_client(supa_url, supa_key)
    ok("Supabase client ready")

    run_integration_test(db)

    # ── Final summary ──────────────────────────────────────────────────────────
    banner("ALL TESTS COMPLETE")
    if unit_failed == 0:
        ok(f"Unit tests  : {unit_passed}/{unit_passed} PASSED")
    else:
        err(f"Unit tests  : {unit_failed} FAILED  ({unit_passed} passed)")
    ok("Integration : completed (check output above for alert counts)")
    print()
    info("Re-run at any time — all DB operations are idempotent.")
    info(f"Supabase dashboard → Table Editor → alerts → filter user_id = {TEST_USER_ID}")
    print()


if __name__ == "__main__":
    main()
