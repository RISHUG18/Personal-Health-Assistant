"""All 13 deterministic alert rules for the Vitalis rules engine.

Each rule is a pure function ``(user_id: str, rows: List[LabRow]) -> AlertRecord``
with NO side effects — no DB access, no I/O.

Rule catalogue
--------------
 1. any_abnormal          — ≥1 row with abnormal_flag=True
 2. low_hemoglobin        — Hgb below config threshold
 3. high_cholesterol      — Total cholesterol elevated (HDL/LDL excluded)
 4. high_ldl              — LDL elevated
 5. low_hdl               — HDL below threshold
 6. high_triglycerides    — Triglycerides elevated
 7. high_blood_sugar      — Fasting/random glucose elevated
 8. high_hba1c            — HbA1c elevated
 9. abnormal_tsh          — TSH outside normal range
10. low_vitamin_d         — Vitamin D below threshold
11. low_b12               — Vitamin B12 below threshold
12. high_creatinine       — Serum creatinine elevated (urine excluded)
13. high_bun              — Blood urea nitrogen elevated
14. high_alt_ast          — ALT/AST elevated
15. high_bilirubin        — Bilirubin elevated
16. low_platelets         — Platelets below threshold
17. abnormal_wbc          — WBC outside normal range
18. missing_critical_tests — No CBC or no metabolic marker present
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional
import json
import os

from backend.rules.models import AlertRecord, Severity

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        RULES_CONFIG = json.load(f)
except Exception:
    RULES_CONFIG = {}


# ---------------------------------------------------------------------------
# LabRow — lightweight value object passed to every rule function
# ---------------------------------------------------------------------------

@dataclass
class LabRow:
    """A single normalised lab result row."""
    lab_result_id:   str
    report_id:       str
    test_name:       str
    value:           Optional[float]
    unit:            Optional[str]       = None
    reference_range: Optional[str]       = None
    abnormal_flag:   Optional[bool]      = None
    report_date:     Optional[str]       = None
    ocr_snippet:     Optional[str]       = None


# ---------------------------------------------------------------------------
# RuleDefinition
# ---------------------------------------------------------------------------

@dataclass
class RuleDefinition:
    rule_id:     str
    description: str
    func:        Callable[[str, List[LabRow]], AlertRecord]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _name(row: LabRow) -> str:
    """Lowercase, stripped test name for fuzzy matching."""
    return (row.test_name or "").lower().strip()


def _no_trigger(rule_id: str) -> AlertRecord:
    return AlertRecord(rule_id=rule_id, triggered=False)


def _trigger(
    rule_id: str,
    severity: Severity,
    reason: str,
    evidence: List[LabRow],
) -> AlertRecord:
    return AlertRecord(
        rule_id=rule_id,
        triggered=True,
        severity=severity,
        reason=reason,
        evidence=evidence,
    )


def _get_cfg(*keys: str) -> dict:
    cfg: object = RULES_CONFIG
    for key in keys:
        if not isinstance(cfg, dict):
            return {}
        cfg = cfg.get(key)
    return cfg if isinstance(cfg, dict) else {}


def _merge_gender_cfg(cfg: dict, direction: str) -> dict:
    """Merge male/female thresholds into a single dict when gender is unknown.

    direction:
        "high" -> choose lower thresholds (more sensitive for high alerts)
        "low"  -> choose higher thresholds (more sensitive for low alerts)
    """
    male_cfg = cfg.get("male") if isinstance(cfg.get("male"), dict) else {}
    female_cfg = cfg.get("female") if isinstance(cfg.get("female"), dict) else {}
    if not male_cfg and not female_cfg:
        return cfg

    merged: dict = {}
    keys = set(male_cfg.keys()) | set(female_cfg.keys())
    for key in keys:
        m_val = male_cfg.get(key)
        f_val = female_cfg.get(key)
        if isinstance(m_val, (int, float)) and isinstance(f_val, (int, float)):
            merged[key] = min(m_val, f_val) if direction == "high" else max(m_val, f_val)
        else:
            merged[key] = m_val if m_val is not None else f_val
    return merged


def _glucose_cfg_for_row(row: LabRow) -> tuple[str, dict]:
    name = _name(row)
    if "random" in name or "rbs" in name:
        return "random", _get_cfg("blood_sugar", "random_glucose")
    return "fasting", _get_cfg("blood_sugar", "fasting_glucose")


# ---------------------------------------------------------------------------
# Rule 1 — any_abnormal
# ---------------------------------------------------------------------------

def _rule_any_abnormal(user_id: str, rows: List[LabRow]) -> AlertRecord:
    bad = [r for r in rows if r.abnormal_flag is True]
    if not bad:
        return _no_trigger("any_abnormal")
    count    = len(bad)
    severity = Severity.HIGH if count >= 3 else Severity.MEDIUM
    names    = ", ".join(r.test_name for r in bad[:3])
    if count > 3:
        names += f" (+{count - 3} more)"
    return _trigger(
        "any_abnormal",
        severity,
        f"{count} abnormal lab value(s) flagged: {names}",
        bad,
    )


# ---------------------------------------------------------------------------
# Rule 2 — low_hemoglobin
# ---------------------------------------------------------------------------

_HGB_INCLUDE = {"hemoglobin", "haemoglobin", "hgb", "hb"}
_HGB_EXCLUDE = {"glycated", "hba", "a1c"}


def _is_hemoglobin(row: LabRow) -> bool:
    n = _name(row)
    if any(ex in n for ex in _HGB_EXCLUDE):
        return False
    return any(kw in n for kw in _HGB_INCLUDE)


def _rule_low_hemoglobin(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_hemoglobin(r) and r.value is not None]
    if not candidates:
        return _no_trigger("low_hemoglobin")
    worst = min(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _merge_gender_cfg(_get_cfg("hematology", "hemoglobin"), "low")
    medium_low = cfg.get("medium_low", 12.0)
    high_low = cfg.get("high_low", 8.0)

    if val >= medium_low:
        return _no_trigger("low_hemoglobin")
    severity = Severity.HIGH if val < high_low else Severity.MEDIUM
    unit     = worst.unit or "g/dL"
    return _trigger(
        "low_hemoglobin",
        severity,
        f"Low hemoglobin: {val} {unit} (normal ≥ 12 g/dL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 3 — high_cholesterol  (total cholesterol; HDL and LDL excluded)
# ---------------------------------------------------------------------------

def _is_total_cholesterol(row: LabRow) -> bool:
    n = _name(row)
    if not ("cholesterol" in n):
        return False
    # Exclude HDL, LDL, VLDL — they have their own rules
    if any(k in n for k in ("hdl", "ldl", "vldl", "high density", "low density")):
        return False
    return True


def _rule_high_cholesterol(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_total_cholesterol(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_cholesterol")
    worst = max(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _get_cfg("lipid_profile", "total_cholesterol")
    medium_high = cfg.get("medium_high", 200)
    high_high = cfg.get("high_high", 240)

    if val < medium_high:
        return _no_trigger("high_cholesterol")
    severity = Severity.HIGH if val >= high_high else Severity.LOW
    label    = "High" if val >= high_high else "Borderline high"
    return _trigger(
        "high_cholesterol",
        severity,
        f"{label} total cholesterol: {val} mg/dL (normal < {medium_high})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 4 — high_ldl
# ---------------------------------------------------------------------------

def _is_ldl(row: LabRow) -> bool:
    n = _name(row)
    return "ldl" in n or "low density lipoprotein" in n


def _rule_high_ldl(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_ldl(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_ldl")
    worst = max(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _get_cfg("lipid_profile", "ldl")
    medium_high = cfg.get("medium_high", 130)
    high_high = cfg.get("high_high", 160)
    critical_high = cfg.get("critical_high", 190)

    if val < medium_high:
        return _no_trigger("high_ldl")
    if val >= critical_high:
        severity = Severity.HIGH
        label = "Very high"
    elif val >= high_high:
        severity = Severity.MEDIUM
        label = "High"
    else:
        severity = Severity.LOW
        label = "Borderline high"
    return _trigger(
        "high_ldl",
        severity,
        f"{label} LDL cholesterol: {val} mg/dL (optimal < {medium_high})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 5 — low_hdl
# ---------------------------------------------------------------------------

_HDL_KEYWORDS = {"hdl", "high density lipoprotein"}


def _is_hdl(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _HDL_KEYWORDS)


def _rule_low_hdl(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_hdl(r) and r.value is not None]
    if not candidates:
        return _no_trigger("low_hdl")
    worst = min(candidates, key=lambda r: r.value)
    val = worst.value

    cfg = _get_cfg("lipid_profile", "hdl")
    merged = _merge_gender_cfg(cfg, "low")
    medium_low = merged.get("medium_low", 40)
    critical_low = cfg.get("critical_low", 30)

    if val >= medium_low:
        return _no_trigger("low_hdl")
    severity = Severity.HIGH if val < critical_low else Severity.MEDIUM
    label = "Severely low" if val < critical_low else "Low"
    return _trigger(
        "low_hdl",
        severity,
        f"{label} HDL cholesterol: {val} mg/dL (normal ≥ {medium_low})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 6 — high_triglycerides
# ---------------------------------------------------------------------------

_TRIGLYCERIDES_KEYWORDS = {"triglyceride", "triglycerides", "tg"}


def _is_triglycerides(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _TRIGLYCERIDES_KEYWORDS)


def _rule_high_triglycerides(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_triglycerides(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_triglycerides")
    worst = max(candidates, key=lambda r: r.value)
    val = worst.value

    cfg = _get_cfg("lipid_profile", "triglycerides")
    medium_high = cfg.get("medium_high", 150)
    high_high = cfg.get("high_high", 200)
    critical_high = cfg.get("critical_high", 500)

    if val < medium_high:
        return _no_trigger("high_triglycerides")
    if val >= critical_high:
        severity = Severity.HIGH
        label = "Very high"
    elif val >= high_high:
        severity = Severity.MEDIUM
        label = "High"
    else:
        severity = Severity.LOW
        label = "Borderline high"
    return _trigger(
        "high_triglycerides",
        severity,
        f"{label} triglycerides: {val} mg/dL (normal < {medium_high})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 7 — high_blood_sugar
# ---------------------------------------------------------------------------

_GLUCOSE_INCLUDE = {"fasting blood glucose", "fbs", "blood glucose", "blood sugar",
                    "glucose", "fasting glucose", "fbg", "rbs", "random blood sugar"}
_GLUCOSE_EXCLUDE = {"urine", "csf"}


def _is_blood_glucose(row: LabRow) -> bool:
    n = _name(row)
    if any(ex in n for ex in _GLUCOSE_EXCLUDE):
        return False
    return any(kw in n for kw in _GLUCOSE_INCLUDE)


def _rule_high_blood_sugar(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_blood_glucose(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_blood_sugar")
    worst = max(candidates, key=lambda r: r.value)
    val   = worst.value
    glucose_kind, cfg = _glucose_cfg_for_row(worst)
    medium_high = cfg.get("medium_high", 100)
    high_high = cfg.get("high_high", 126)

    if val < medium_high:
        return _no_trigger("high_blood_sugar")
    severity = Severity.HIGH if val >= high_high else Severity.MEDIUM
    label    = "Diabetic range" if val >= high_high else "Pre-diabetic range"
    return _trigger(
        "high_blood_sugar",
        severity,
        f"{label} {glucose_kind} blood glucose: {val} mg/dL (normal < {medium_high})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 8 — high_hba1c
# ---------------------------------------------------------------------------

_HBA1C_KEYWORDS = {"hba1c", "hba 1c", "a1c", "glycated hemoglobin",
                   "glycated haemoglobin", "glycosylated hemoglobin", "hb a1c"}


def _is_hba1c(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _HBA1C_KEYWORDS)


def _rule_high_hba1c(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_hba1c(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_hba1c")
    worst = max(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _get_cfg("blood_sugar", "hba1c")
    medium_high = cfg.get("medium_high", 5.7)
    high_high = cfg.get("high_high", 6.5)

    if val < medium_high:
        return _no_trigger("high_hba1c")
    severity = Severity.HIGH if val >= high_high else Severity.MEDIUM
    label    = "Diabetic range" if val >= high_high else "Pre-diabetic range"
    return _trigger(
        "high_hba1c",
        severity,
        f"{label} HbA1c: {val}% (normal < {medium_high}%)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 9 — abnormal_tsh
# ---------------------------------------------------------------------------

_TSH_KEYWORDS = {"tsh", "thyroid stimulating hormone", "thyrotropin"}


def _is_tsh(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _TSH_KEYWORDS)


def _rule_abnormal_tsh(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_tsh(r) and r.value is not None]
    if not candidates:
        return _no_trigger("abnormal_tsh")
    # Use the most abnormal value (furthest from midpoint 2.45)
    worst = max(candidates, key=lambda r: abs(r.value - 2.45))
    val   = worst.value
    cfg = _get_cfg("thyroid", "tsh")
    low_cutoff = cfg.get("low", 0.4)
    high_cutoff = cfg.get("high", 4.5)
    severe_high = cfg.get("critical_high", 10)
    if low_cutoff <= val <= high_cutoff:
        return _no_trigger("abnormal_tsh")
    if val > severe_high:
        severity = Severity.HIGH
        label    = f"Severely elevated TSH (hypothyroid): {val} µIU/mL"
    elif val > high_cutoff:
        severity = Severity.MEDIUM
        label    = f"Elevated TSH (hypothyroid): {val} µIU/mL"
    else:  # val < low_cutoff
        severity = Severity.MEDIUM
        label    = f"Suppressed TSH (hyperthyroid): {val} µIU/mL"
    return _trigger(
        "abnormal_tsh",
        severity,
        f"{label} (normal {low_cutoff}–{high_cutoff} µIU/mL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 10 — low_vitamin_d
# ---------------------------------------------------------------------------

_VITD_KEYWORDS = {"vitamin d", "vit d", "25(oh)", "25-oh", "25 oh",
                  "calcidiol", "cholecalciferol"}


def _is_vitamin_d(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _VITD_KEYWORDS)


def _rule_low_vitamin_d(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_vitamin_d(r) and r.value is not None]
    if not candidates:
        return _no_trigger("low_vitamin_d")
    worst = min(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _get_cfg("vitamins", "vitamin_d")
    medium_low = cfg.get("medium_low", 30)
    high_low = cfg.get("high_low", 12)
    if val >= medium_low:
        return _no_trigger("low_vitamin_d")
    severity = Severity.HIGH if val < high_low else Severity.MEDIUM
    label    = "Severely deficient" if val < high_low else "Insufficient"
    unit     = worst.unit or "ng/mL"
    return _trigger(
        "low_vitamin_d",
        severity,
        f"{label} Vitamin D: {val} {unit} (sufficient ≥ {medium_low} ng/mL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 11 — low_b12
# ---------------------------------------------------------------------------

_B12_KEYWORDS = {"vitamin b12", "b12", "b-12", "cobalamin",
                 "cyanocobalamin", "methylcobalamin"}


def _is_b12(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _B12_KEYWORDS)


def _rule_low_b12(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_b12(r) and r.value is not None]
    if not candidates:
        return _no_trigger("low_b12")
    worst = min(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _get_cfg("vitamins", "b12")
    medium_low = cfg.get("medium_low", 300)
    high_low = cfg.get("high_low", 150)
    if val >= medium_low:
        return _no_trigger("low_b12")
    severity = Severity.HIGH if val < high_low else Severity.MEDIUM
    label    = "Severely low" if val < high_low else "Low"
    unit     = worst.unit or "pg/mL"
    return _trigger(
        "low_b12",
        severity,
        f"{label} Vitamin B12: {val} {unit} (normal ≥ {medium_low} pg/mL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 12 — high_creatinine  (serum only; urine excluded)
# ---------------------------------------------------------------------------

def _is_serum_creatinine(row: LabRow) -> bool:
    n = _name(row)
    if "urine" in n or "urinary" in n or "ur " in n:
        return False
    return "creatinine" in n


def _rule_high_creatinine(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_serum_creatinine(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_creatinine")
    worst = max(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _merge_gender_cfg(_get_cfg("kidney_function", "creatinine"), "high")
    medium_high = cfg.get("medium_high", 1.2)
    high_high = cfg.get("high_high", 2.0)

    if val < medium_high:
        return _no_trigger("high_creatinine")
    severity = Severity.HIGH if val >= high_high else Severity.MEDIUM
    label    = "Severely elevated" if val >= high_high else "Elevated"
    unit     = worst.unit or "mg/dL"
    return _trigger(
        "high_creatinine",
        severity,
        f"{label} serum creatinine: {val} {unit} (normal < {medium_high} mg/dL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 13 — high_bun
# ---------------------------------------------------------------------------

_BUN_KEYWORDS = {"bun", "blood urea nitrogen", "urea nitrogen"}


def _is_bun(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _BUN_KEYWORDS)


def _rule_high_bun(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_bun(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_bun")
    worst = max(candidates, key=lambda r: r.value)
    val = worst.value

    cfg = _get_cfg("kidney_function", "bun")
    medium_high = cfg.get("medium_high", 20)
    high_high = cfg.get("high_high", 40)

    if val < medium_high:
        return _no_trigger("high_bun")
    severity = Severity.HIGH if val >= high_high else Severity.MEDIUM
    label = "Severely elevated" if val >= high_high else "Elevated"
    return _trigger(
        "high_bun",
        severity,
        f"{label} BUN: {val} mg/dL (normal < {medium_high})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 14 — high_alt_ast
# ---------------------------------------------------------------------------

_ALT_AST_KEYWORDS = {
    "alt", "ast", "sgpt", "sgot",
    "alanine aminotransferase", "aspartate aminotransferase",
}


def _is_alt_ast(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _ALT_AST_KEYWORDS)


def _rule_high_alt_ast(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_alt_ast(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_alt_ast")
    worst = max(candidates, key=lambda r: r.value)
    val = worst.value

    cfg = _get_cfg("liver_function", "alt_ast")
    medium_high = cfg.get("medium_high", 40)
    high_high = cfg.get("high_high", 100)

    if val < medium_high:
        return _no_trigger("high_alt_ast")
    severity = Severity.HIGH if val >= high_high else Severity.MEDIUM
    label = "Severely elevated" if val >= high_high else "Elevated"
    return _trigger(
        "high_alt_ast",
        severity,
        f"{label} ALT/AST: {val} U/L (normal < {medium_high})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 15 — high_bilirubin
# ---------------------------------------------------------------------------

_BILIRUBIN_KEYWORDS = {"bilirubin", "total bilirubin"}


def _is_bilirubin(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _BILIRUBIN_KEYWORDS)


def _rule_high_bilirubin(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_bilirubin(r) and r.value is not None]
    if not candidates:
        return _no_trigger("high_bilirubin")
    worst = max(candidates, key=lambda r: r.value)
    val = worst.value

    cfg = _get_cfg("liver_function", "bilirubin")
    medium_high = cfg.get("medium_high", 1.2)
    high_high = cfg.get("high_high", 3.0)

    if val < medium_high:
        return _no_trigger("high_bilirubin")
    severity = Severity.HIGH if val >= high_high else Severity.MEDIUM
    label = "Severely elevated" if val >= high_high else "Elevated"
    return _trigger(
        "high_bilirubin",
        severity,
        f"{label} bilirubin: {val} mg/dL (normal < {medium_high})",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 16 — low_platelets
# ---------------------------------------------------------------------------

def _is_platelet(row: LabRow) -> bool:
    n = _name(row)
    return "platelet" in n or n.strip() == "plt"


def _rule_low_platelets(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_platelet(r) and r.value is not None]
    if not candidates:
        return _no_trigger("low_platelets")
    worst = min(candidates, key=lambda r: r.value)
    val   = worst.value
    cfg = _get_cfg("hematology", "platelets")
    medium_low = cfg.get("medium_low", 150000) / 1000
    high_low = cfg.get("high_low", 50000) / 1000

    if val >= medium_low:
        return _no_trigger("low_platelets")
    severity = Severity.HIGH if val < high_low else Severity.MEDIUM
    label    = "Critically low" if val < high_low else "Low"
    unit     = worst.unit or "×10³/µL"
    return _trigger(
        "low_platelets",
        severity,
        f"{label} platelet count: {val} {unit} (normal {medium_low}–400 ×10³/µL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 17 — abnormal_wbc
# ---------------------------------------------------------------------------

_WBC_KEYWORDS = {"wbc", "white blood cell", "leucocyte", "leukocyte",
                 "total leucocyte", "total leukocyte", "tlc"}


def _is_wbc(row: LabRow) -> bool:
    n = _name(row)
    return any(kw in n for kw in _WBC_KEYWORDS)


def _rule_abnormal_wbc(user_id: str, rows: List[LabRow]) -> AlertRecord:
    candidates = [r for r in rows if _is_wbc(r) and r.value is not None]
    if not candidates:
        return _no_trigger("abnormal_wbc")
    worst = max(candidates, key=lambda r: abs(r.value - 6.5))  # midpoint ~6.5
    val   = worst.value
    cfg = _get_cfg("hematology", "wbc")
    medium_low = cfg.get("medium_low", 4000) / 1000
    medium_high = cfg.get("medium_high", 11000) / 1000
    high_high = cfg.get("high_high", 20000) / 1000

    if medium_low <= val <= medium_high:
        return _no_trigger("abnormal_wbc")
    if val > high_high or val < (medium_low / 2):
        severity = Severity.HIGH
    else:
        severity = Severity.MEDIUM
    direction = "Elevated" if val > medium_high else "Low"
    unit      = worst.unit or "×10³/µL"
    return _trigger(
        "abnormal_wbc",
        severity,
        f"{direction} WBC count: {val} {unit} (normal {medium_low}–{medium_high} ×10³/µL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 18 — missing_critical_tests
# ---------------------------------------------------------------------------

_CBC_KEYWORDS      = {"hemoglobin", "haemoglobin", "hgb", "hb",
                      "wbc", "leucocyte", "leukocyte", "platelet", "plt", "rbc"}
_METABOLIC_KEYWORDS = {"glucose", "fbs", "fbg", "blood sugar",
                       "hba1c", "hba 1c", "a1c", "glycated",
                       "cholesterol", "triglyceride"}


def _rule_missing_critical_tests(user_id: str, rows: List[LabRow]) -> AlertRecord:
    names = [_name(r) for r in rows]

    has_cbc      = any(any(kw in n for kw in _CBC_KEYWORDS) for n in names)
    has_metabolic = any(any(kw in n for kw in _METABOLIC_KEYWORDS) for n in names)

    missing = []
    if not has_cbc:
        missing.append("CBC (hemoglobin/WBC)")
    if not has_metabolic:
        missing.append("metabolic panel (glucose/HbA1c/cholesterol)")

    if not missing:
        return _no_trigger("missing_critical_tests")

    return _trigger(
        "missing_critical_tests",
        Severity.LOW,
        f"Missing critical test group(s): {', '.join(missing)}",
        [],  # no specific lab rows to cite
    )


# ---------------------------------------------------------------------------
# ALL_RULES — ordered list consumed by the engine
# ---------------------------------------------------------------------------

ALL_RULES: List[RuleDefinition] = [
    RuleDefinition("any_abnormal",           "Any lab value flagged as abnormal",          _rule_any_abnormal),
    RuleDefinition("low_hemoglobin",         "Hemoglobin below normal range",               _rule_low_hemoglobin),
    RuleDefinition("high_cholesterol",       "Total cholesterol elevated",                  _rule_high_cholesterol),
    RuleDefinition("high_ldl",               "LDL cholesterol elevated",                    _rule_high_ldl),
    RuleDefinition("low_hdl",                "HDL cholesterol below normal range",          _rule_low_hdl),
    RuleDefinition("high_triglycerides",     "Triglycerides elevated",                      _rule_high_triglycerides),
    RuleDefinition("high_blood_sugar",       "Fasting blood glucose elevated",              _rule_high_blood_sugar),
    RuleDefinition("high_hba1c",             "HbA1c indicates pre-diabetes or diabetes",   _rule_high_hba1c),
    RuleDefinition("abnormal_tsh",           "TSH outside normal range",                    _rule_abnormal_tsh),
    RuleDefinition("low_vitamin_d",          "Vitamin D insufficient or deficient",         _rule_low_vitamin_d),
    RuleDefinition("low_b12",                "Vitamin B12 below normal range",              _rule_low_b12),
    RuleDefinition("high_creatinine",        "Serum creatinine elevated (kidney function)", _rule_high_creatinine),
    RuleDefinition("high_bun",               "BUN elevated",                                _rule_high_bun),
    RuleDefinition("high_alt_ast",           "ALT/AST elevated",                            _rule_high_alt_ast),
    RuleDefinition("high_bilirubin",         "Bilirubin elevated",                          _rule_high_bilirubin),
    RuleDefinition("low_platelets",          "Platelet count below normal range",           _rule_low_platelets),
    RuleDefinition("abnormal_wbc",           "WBC count outside normal range",              _rule_abnormal_wbc),
    RuleDefinition("missing_critical_tests", "Critical test groups absent from reports",    _rule_missing_critical_tests),
]
