"""All 13 deterministic alert rules for the Vitalis rules engine.

Each rule is a pure function ``(user_id: str, rows: List[LabRow]) -> AlertRecord``
with NO side effects — no DB access, no I/O.

Rule catalogue
--------------
 1. any_abnormal          — ≥1 row with abnormal_flag=True
 2. low_hemoglobin        — Hgb < 12 g/dL
 3. high_cholesterol      — Total cholesterol ≥ 200 (HDL/LDL excluded)
 4. high_ldl              — LDL ≥ 160
 5. high_blood_sugar      — Fasting glucose ≥ 100
 6. high_hba1c            — HbA1c ≥ 5.7 %
 7. abnormal_tsh          — TSH < 0.4 or > 4.5 µIU/mL
 8. low_vitamin_d         — Vit D < 30 ng/mL
 9. low_b12               — B12 < 300 pg/mL
10. high_creatinine       — Serum creatinine ≥ 1.3 (urine excluded)
11. low_platelets         — Platelets < 150 ×10³/µL
12. abnormal_wbc          — WBC < 2 or > 11 ×10³/µL
13. missing_critical_tests — No CBC or no metabolic marker present
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from backend.rules.models import AlertRecord, Severity


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
    if val >= 12.0:
        return _no_trigger("low_hemoglobin")
    severity = Severity.HIGH if val < 8.0 else Severity.MEDIUM
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
    if val < 200:
        return _no_trigger("high_cholesterol")
    severity = Severity.HIGH if val > 240 else Severity.LOW
    label    = "High" if val > 240 else "Borderline high"
    return _trigger(
        "high_cholesterol",
        severity,
        f"{label} total cholesterol: {val} mg/dL (normal < 200)",
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
    if val < 160:
        return _no_trigger("high_ldl")
    severity = Severity.HIGH if val > 190 else Severity.MEDIUM
    label    = "Very high" if val > 190 else "High"
    return _trigger(
        "high_ldl",
        severity,
        f"{label} LDL cholesterol: {val} mg/dL (optimal < 100)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 5 — high_blood_sugar
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
    if val < 100:
        return _no_trigger("high_blood_sugar")
    severity = Severity.HIGH if val > 126 else Severity.MEDIUM
    label    = "Diabetic range" if val > 126 else "Pre-diabetic range"
    return _trigger(
        "high_blood_sugar",
        severity,
        f"{label} fasting blood glucose: {val} mg/dL (normal < 100)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 6 — high_hba1c
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
    if val < 5.7:
        return _no_trigger("high_hba1c")
    severity = Severity.HIGH if val >= 6.5 else Severity.MEDIUM
    label    = "Diabetic range" if val >= 6.5 else "Pre-diabetic range"
    return _trigger(
        "high_hba1c",
        severity,
        f"{label} HbA1c: {val}% (normal < 5.7%)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 7 — abnormal_tsh
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
    if 0.4 <= val <= 4.5:
        return _no_trigger("abnormal_tsh")
    if val > 10:
        severity = Severity.HIGH
        label    = f"Severely elevated TSH (hypothyroid): {val} µIU/mL"
    elif val > 4.5:
        severity = Severity.MEDIUM
        label    = f"Elevated TSH (hypothyroid): {val} µIU/mL"
    else:  # val < 0.4
        severity = Severity.MEDIUM
        label    = f"Suppressed TSH (hyperthyroid): {val} µIU/mL"
    return _trigger(
        "abnormal_tsh",
        severity,
        f"{label} (normal 0.4–4.5 µIU/mL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 8 — low_vitamin_d
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
    if val >= 30:
        return _no_trigger("low_vitamin_d")
    severity = Severity.HIGH if val < 12 else Severity.MEDIUM
    label    = "Severely deficient" if val < 12 else "Insufficient"
    unit     = worst.unit or "ng/mL"
    return _trigger(
        "low_vitamin_d",
        severity,
        f"{label} Vitamin D: {val} {unit} (sufficient ≥ 30 ng/mL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 9 — low_b12
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
    if val >= 300:
        return _no_trigger("low_b12")
    severity = Severity.HIGH if val < 150 else Severity.MEDIUM
    label    = "Severely low" if val < 150 else "Low"
    unit     = worst.unit or "pg/mL"
    return _trigger(
        "low_b12",
        severity,
        f"{label} Vitamin B12: {val} {unit} (normal ≥ 300 pg/mL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 10 — high_creatinine  (serum only; urine excluded)
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
    if val < 1.3:
        return _no_trigger("high_creatinine")
    severity = Severity.HIGH if val > 2.0 else Severity.MEDIUM
    label    = "Severely elevated" if val > 2.0 else "Elevated"
    unit     = worst.unit or "mg/dL"
    return _trigger(
        "high_creatinine",
        severity,
        f"{label} serum creatinine: {val} {unit} (normal < 1.2 mg/dL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 11 — low_platelets
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
    if val >= 150:
        return _no_trigger("low_platelets")
    severity = Severity.HIGH if val < 50 else Severity.MEDIUM
    label    = "Critically low" if val < 50 else "Low"
    unit     = worst.unit or "×10³/µL"
    return _trigger(
        "low_platelets",
        severity,
        f"{label} platelet count: {val} {unit} (normal 150–400 ×10³/µL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 12 — abnormal_wbc
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
    if 2.0 <= val <= 11.0:
        return _no_trigger("abnormal_wbc")
    if val > 15 or val < 2:
        severity = Severity.HIGH
    else:
        severity = Severity.MEDIUM
    direction = "Elevated" if val > 11 else "Low"
    unit      = worst.unit or "×10³/µL"
    return _trigger(
        "abnormal_wbc",
        severity,
        f"{direction} WBC count: {val} {unit} (normal 4–11 ×10³/µL)",
        [worst],
    )


# ---------------------------------------------------------------------------
# Rule 13 — missing_critical_tests
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
    RuleDefinition("high_blood_sugar",       "Fasting blood glucose elevated",              _rule_high_blood_sugar),
    RuleDefinition("high_hba1c",             "HbA1c indicates pre-diabetes or diabetes",   _rule_high_hba1c),
    RuleDefinition("abnormal_tsh",           "TSH outside normal range",                    _rule_abnormal_tsh),
    RuleDefinition("low_vitamin_d",          "Vitamin D insufficient or deficient",         _rule_low_vitamin_d),
    RuleDefinition("low_b12",                "Vitamin B12 below normal range",              _rule_low_b12),
    RuleDefinition("high_creatinine",        "Serum creatinine elevated (kidney function)", _rule_high_creatinine),
    RuleDefinition("low_platelets",          "Platelet count below normal range",           _rule_low_platelets),
    RuleDefinition("abnormal_wbc",           "WBC count outside normal range",              _rule_abnormal_wbc),
    RuleDefinition("missing_critical_tests", "Critical test groups absent from reports",    _rule_missing_critical_tests),
]
