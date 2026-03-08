"""Predefined rule definitions for lab result analysis.

Each rule is a pure function: (user_id, List[LabRow]) → RuleResult.
No I/O, no side effects.  This makes rules trivially unit-testable.

Rule categories
---------------
general      : any_abnormal — fires when ≥1 result is flagged abnormal
cbc          : low_hemoglobin, low_platelets, abnormal_wbc
lipid        : high_cholesterol, high_ldl
metabolic    : high_blood_sugar, high_hba1c, high_creatinine
thyroid      : abnormal_tsh
micronutrient: low_vitamin_d, low_b12
data_quality : missing_critical_tests

Severity tiers (for reference)
--------------------------------
HIGH   — critical threshold crossed; prompt review warranted
MEDIUM — borderline / moderate deviation
LOW    — informational; worth noting

Thresholds used are standard clinical reference ranges.
They are NOT diagnostic — always consult a qualified clinician.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .models import EvidenceRef, RuleResult, Severity


# ── Data carrier ─────────────────────────────────────────────────────────────


@dataclass
class LabRow:
    """A flattened view of one lab_results row joined with its parent report.

    Populated by the engine before rules are evaluated; rules receive a list
    of these and must not modify them.
    """

    lab_result_id: str
    report_id: str
    test_name: str
    value: Optional[float]
    unit: Optional[str]
    reference_range: Optional[str]
    abnormal_flag: Optional[bool]
    report_date: Optional[str]
    ocr_snippet: Optional[str] = None  # ≤200-char verbatim OCR line


# Rule callable type alias
RuleFunc = Callable[[str, List[LabRow]], RuleResult]


@dataclass
class RuleDefinition:
    """Metadata + callable for a single rule."""

    rule_id: str
    description: str
    func: RuleFunc
    tags: List[str] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _matches(test_name: str, *patterns: str) -> bool:
    """Return True if any pattern appears (case-insensitively) in test_name."""
    tn = test_name.lower()
    return any(p.lower() in tn for p in patterns)


def _find_rows(rows: List[LabRow], *patterns: str) -> List[LabRow]:
    """Filter rows whose test_name matches any of the given patterns."""
    return [r for r in rows if _matches(r.test_name, *patterns)]


def _ref(r: LabRow) -> EvidenceRef:
    """Shorthand: build an EvidenceRef from a LabRow."""
    return EvidenceRef(
        report_id=r.report_id,
        lab_result_id=r.lab_result_id,
        ocr_text_snippet=r.ocr_snippet,
    )


# ── Rule implementations ──────────────────────────────────────────────────────

# ── RULE: any_abnormal ────────────────────────────────────────────────────────


def _rule_any_abnormal(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Fire when at least one lab result carries an explicit abnormal flag.

    The flag is set by the Gemini extraction layer when the report itself
    marks a result with H / L / * / ↑ / ↓.  This rule does NOT compute
    abnormality — it only reflects what the source document stated.

    Severity escalates with count:
        1-2 abnormal → MEDIUM
        3+  abnormal → HIGH
    """
    triggered = [r for r in rows if r.abnormal_flag is True]
    if not triggered:
        return RuleResult(rule_id="any_abnormal", triggered=False)

    count = len(triggered)
    names = ", ".join(r.test_name for r in triggered[:5])
    extra = f" (+{count - 5} more)" if count > 5 else ""

    return RuleResult(
        rule_id="any_abnormal",
        triggered=True,
        severity=Severity.MEDIUM if count <= 2 else Severity.HIGH,
        reason=f"{count} lab result(s) flagged abnormal by the report: {names}{extra}.",
        evidence_refs=[_ref(r) for r in triggered],
    )


# ── RULE: low_hemoglobin ─────────────────────────────────────────────────────


def _rule_low_hemoglobin(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Hemoglobin below clinical thresholds.

    < 8 g/dL  → HIGH   (critical anemia)
    < 12 g/dL → MEDIUM (mild-moderate anemia; uses female lower bound)
    """
    matches = _find_rows(rows, "hemoglobin", "haemoglobin", "hgb", "hb")
    for r in matches:
        if r.value is None:
            continue
        if r.value < 8.0:
            return RuleResult(
                rule_id="low_hemoglobin",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Critically low Hemoglobin: {r.value} {r.unit or ''}. "
                    "Normal ≥ 12 g/dL. Possible severe anemia — prompt review advised."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value < 12.0:
            return RuleResult(
                rule_id="low_hemoglobin",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"Low Hemoglobin: {r.value} {r.unit or ''} "
                    "(below 12 g/dL threshold). Possible anemia."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="low_hemoglobin", triggered=False)


# ── RULE: high_cholesterol ───────────────────────────────────────────────────


def _rule_high_cholesterol(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Total cholesterol above desirable range.

    > 240 mg/dL → HIGH   (high cardiovascular risk)
    > 200 mg/dL → LOW    (borderline — watch and diet)
    HDL / LDL / VLDL sub-fraction rows are excluded.
    """
    matches = _find_rows(rows, "total cholesterol", "cholesterol")
    matches = [r for r in matches if not _matches(r.test_name, "hdl", "ldl", "vldl", "non-hdl")]

    for r in matches:
        if r.value is None:
            continue
        if r.value > 240:
            return RuleResult(
                rule_id="high_cholesterol",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"High Total Cholesterol: {r.value} {r.unit or ''} (> 240 mg/dL). "
                    "Elevated cardiovascular risk."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value > 200:
            return RuleResult(
                rule_id="high_cholesterol",
                triggered=True,
                severity=Severity.LOW,
                reason=(
                    f"Borderline Total Cholesterol: {r.value} {r.unit or ''} "
                    "(200–240 mg/dL). Consider dietary review."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="high_cholesterol", triggered=False)


# ── RULE: high_ldl ───────────────────────────────────────────────────────────


def _rule_high_ldl(user_id: str, rows: List[LabRow]) -> RuleResult:
    """LDL cholesterol above safe range.

    > 190 mg/dL → HIGH   (very high; consider statins)
    > 160 mg/dL → MEDIUM (high range)
    """
    matches = _find_rows(rows, "ldl")
    for r in matches:
        if r.value is None:
            continue
        if r.value > 190:
            return RuleResult(
                rule_id="high_ldl",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Very High LDL Cholesterol: {r.value} {r.unit or ''} (> 190 mg/dL). "
                    "High cardiovascular risk; statin therapy may be warranted."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value > 160:
            return RuleResult(
                rule_id="high_ldl",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"High LDL Cholesterol: {r.value} {r.unit or ''} (160–190 mg/dL). "
                    "Above desirable range."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="high_ldl", triggered=False)


# ── RULE: high_blood_sugar ───────────────────────────────────────────────────


def _rule_high_blood_sugar(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Fasting blood glucose above normal range.

    > 126 mg/dL → HIGH   (diabetes diagnostic range)
    > 100 mg/dL → MEDIUM (impaired fasting glucose / pre-diabetes)
    """
    matches = _find_rows(
        rows, "glucose", "blood sugar", "fasting sugar", "fbs", "blood glucose"
    )
    for r in matches:
        if r.value is None:
            continue
        if r.value > 126:
            return RuleResult(
                rule_id="high_blood_sugar",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Elevated Fasting Blood Glucose: {r.value} {r.unit or ''} (> 126 mg/dL). "
                    "Consistent with diabetes diagnostic criteria."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value > 100:
            return RuleResult(
                rule_id="high_blood_sugar",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"Impaired Fasting Glucose: {r.value} {r.unit or ''} (100–126 mg/dL). "
                    "Pre-diabetic range."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="high_blood_sugar", triggered=False)


# ── RULE: high_hba1c ─────────────────────────────────────────────────────────


def _rule_high_hba1c(user_id: str, rows: List[LabRow]) -> RuleResult:
    """HbA1c percentage above normal.

    ≥ 6.5% → HIGH   (WHO diabetes diagnostic threshold)
    ≥ 5.7% → MEDIUM (pre-diabetes range per ADA)
    """
    matches = _find_rows(rows, "hba1c", "hb a1c", "glycated", "glycosylated", "a1c")
    for r in matches:
        if r.value is None:
            continue
        if r.value >= 6.5:
            return RuleResult(
                rule_id="high_hba1c",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Elevated HbA1c: {r.value}% (≥ 6.5%). "
                    "Meets WHO diagnostic threshold for diabetes mellitus."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value >= 5.7:
            return RuleResult(
                rule_id="high_hba1c",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"Pre-Diabetic HbA1c: {r.value}% (5.7–6.4%). "
                    "Elevated risk; lifestyle intervention recommended."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="high_hba1c", triggered=False)


# ── RULE: abnormal_tsh ───────────────────────────────────────────────────────


def _rule_abnormal_tsh(user_id: str, rows: List[LabRow]) -> RuleResult:
    """TSH outside the normal range (0.4–4.5 µIU/mL).

    > 10.0       → HIGH   (possible severe hypothyroidism)
    > 4.5 / < 0.4 → MEDIUM (borderline hypo or hyperthyroidism)
    """
    matches = _find_rows(rows, "tsh", "thyroid stimulating", "thyroid stim")
    for r in matches:
        if r.value is None:
            continue
        if r.value > 10.0:
            return RuleResult(
                rule_id="abnormal_tsh",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Critically High TSH: {r.value} {r.unit or ''} (> 10 µIU/mL). "
                    "Consistent with severe hypothyroidism."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value > 4.5 or r.value < 0.4:
            direction = "High" if r.value > 4.5 else "Low"
            condition = "hypothyroidism" if r.value > 4.5 else "hyperthyroidism"
            return RuleResult(
                rule_id="abnormal_tsh",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"{direction} TSH: {r.value} {r.unit or ''} "
                    f"(normal 0.4–4.5 µIU/mL). Possible {condition}."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="abnormal_tsh", triggered=False)


# ── RULE: low_vitamin_d ──────────────────────────────────────────────────────


def _rule_low_vitamin_d(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Vitamin D below adequate levels.

    < 12 (ng/mL or nmol/L) → HIGH   (severe deficiency)
    < 30                    → MEDIUM (insufficiency)

    Note: ng/mL and nmol/L share similar numeric ranges on most Indian
    lab reports (values in the 10–80 range); the rule applies a single
    threshold set appropriate for either unit.
    """
    matches = _find_rows(
        rows, "vitamin d", "vit d", "25-oh", "25(oh)", "25 oh", "cholecalciferol", "calcidiol"
    )
    for r in matches:
        if r.value is None:
            continue
        if r.value < 12:
            return RuleResult(
                rule_id="low_vitamin_d",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Severe Vitamin D Deficiency: {r.value} {r.unit or ''}. "
                    "Supplementation and clinical review strongly advised."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value < 30:
            return RuleResult(
                rule_id="low_vitamin_d",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"Vitamin D Insufficiency: {r.value} {r.unit or ''} "
                    "(< 30). Below optimal level — consider supplementation."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="low_vitamin_d", triggered=False)


# ── RULE: low_b12 ────────────────────────────────────────────────────────────


def _rule_low_b12(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Vitamin B12 below adequate levels.

    < 150 pg/mL → HIGH   (severe deficiency — neurological risk)
    < 300 pg/mL → MEDIUM (sub-optimal; common in vegetarians)
    """
    matches = _find_rows(rows, "b12", "vitamin b12", "vit b12", "cobalamin", "cyanocobalamin")
    for r in matches:
        if r.value is None:
            continue
        if r.value < 150:
            return RuleResult(
                rule_id="low_b12",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Severe Vitamin B12 Deficiency: {r.value} {r.unit or ''} (< 150 pg/mL). "
                    "Risk of neurological complications."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value < 300:
            return RuleResult(
                rule_id="low_b12",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"Low Vitamin B12: {r.value} {r.unit or ''} "
                    "(150–300 pg/mL). Below adequate range."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="low_b12", triggered=False)


# ── RULE: high_creatinine ────────────────────────────────────────────────────


def _rule_high_creatinine(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Serum creatinine above normal (kidney function marker).

    > 2.0 mg/dL → HIGH   (possible moderate-severe kidney impairment)
    > 1.3 mg/dL → MEDIUM (elevated; monitor kidney function)
    Urine creatinine rows are excluded (different reference range).
    """
    matches = _find_rows(rows, "creatinine", "creat")
    matches = [r for r in matches if not _matches(r.test_name, "urine", "spot", "clearance")]

    for r in matches:
        if r.value is None:
            continue
        if r.value > 2.0:
            return RuleResult(
                rule_id="high_creatinine",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Critically High Serum Creatinine: {r.value} {r.unit or ''} (> 2.0 mg/dL). "
                    "Possible moderate-to-severe kidney impairment."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value > 1.3:
            return RuleResult(
                rule_id="high_creatinine",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"Elevated Serum Creatinine: {r.value} {r.unit or ''} "
                    "(1.3–2.0 mg/dL). Monitor kidney function."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="high_creatinine", triggered=False)


# ── RULE: low_platelets ──────────────────────────────────────────────────────


def _rule_low_platelets(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Platelet count below normal (thrombocytopenia).

    Values are expected in ×10³/µL units (i.e., 150 = 150,000/µL).

    < 50  → HIGH   (critical; risk of spontaneous bleeding)
    < 150 → MEDIUM (thrombocytopenia)
    """
    matches = _find_rows(rows, "platelet", "plt", "thrombocyte")
    for r in matches:
        if r.value is None:
            continue
        if r.value < 50:
            return RuleResult(
                rule_id="low_platelets",
                triggered=True,
                severity=Severity.HIGH,
                reason=(
                    f"Critically Low Platelet Count: {r.value} {r.unit or ''} "
                    "(< 50×10³/µL). High risk of bleeding."
                ),
                evidence_refs=[_ref(r)],
            )
        if r.value < 150:
            return RuleResult(
                rule_id="low_platelets",
                triggered=True,
                severity=Severity.MEDIUM,
                reason=(
                    f"Low Platelet Count (Thrombocytopenia): {r.value} {r.unit or ''} "
                    "(< 150×10³/µL). Monitor for bleeding symptoms."
                ),
                evidence_refs=[_ref(r)],
            )
    return RuleResult(rule_id="low_platelets", triggered=False)


# ── RULE: abnormal_wbc ───────────────────────────────────────────────────────


def _rule_abnormal_wbc(user_id: str, rows: List[LabRow]) -> RuleResult:
    """WBC count outside normal range (4–11 ×10³/µL).

    > 15 or < 2  → HIGH   (severe leukocytosis / leukopenia)
    > 11 or < 4  → MEDIUM (borderline)
    """
    matches = _find_rows(
        rows,
        "wbc",
        "white blood cell",
        "white blood count",
        "total leucocyte",
        "total leukocyte",
        "tlc",
    )
    for r in matches:
        if r.value is None:
            continue
        high = r.value > 11
        low = r.value < 4
        if not (high or low):
            continue
        direction = "High" if high else "Low"
        critical = r.value > 15 or r.value < 2
        return RuleResult(
            rule_id="abnormal_wbc",
            triggered=True,
            severity=Severity.HIGH if critical else Severity.MEDIUM,
            reason=(
                f"{'Critically ' if critical else ''}{direction} WBC Count: "
                f"{r.value} {r.unit or ''} (normal 4–11 ×10³/µL). "
                "Possible infection, immune disorder, or bone marrow issue."
            ),
            evidence_refs=[_ref(r)],
        )
    return RuleResult(rule_id="abnormal_wbc", triggered=False)


# ── RULE: missing_critical_tests ─────────────────────────────────────────────


def _rule_missing_critical_tests(user_id: str, rows: List[LabRow]) -> RuleResult:
    """Fire when no results exist for critical test categories.

    Checks for the two most common test families:
      - CBC:       hemoglobin / WBC / platelet
      - Metabolic: glucose / creatinine / cholesterol / liver enzymes

    A missing category usually means either:
      (a) Those tests were not ordered in this report, or
      (b) Extraction failed silently.

    Severity is LOW — informational only.
    """
    has_cbc = any(
        _matches(r.test_name, "hemoglobin", "haemoglobin", "hgb", "wbc", "platelet", "rbc")
        for r in rows
    )
    has_metabolic = any(
        _matches(r.test_name, "glucose", "creatinine", "cholesterol", "sgpt", "alt", "ast", "sgot")
        for r in rows
    )

    missing = []
    if not has_cbc:
        missing.append("CBC (Hemoglobin / WBC / Platelet)")
    if not has_metabolic:
        missing.append("Metabolic panel (Glucose / Cholesterol / Creatinine / Liver enzymes)")

    if missing:
        return RuleResult(
            rule_id="missing_critical_tests",
            triggered=True,
            severity=Severity.LOW,
            reason=(
                f"No extracted results found for: {'; '.join(missing)}. "
                "These tests may not have been ordered, or extraction may be incomplete."
            ),
            evidence_refs=[],
        )
    return RuleResult(rule_id="missing_critical_tests", triggered=False)


# ── Rule registry ─────────────────────────────────────────────────────────────

ALL_RULES: List[RuleDefinition] = [
    RuleDefinition(
        "any_abnormal",
        "Any lab result explicitly flagged abnormal by the report",
        _rule_any_abnormal,
        ["general"],
    ),
    RuleDefinition(
        "low_hemoglobin",
        "Hemoglobin below clinical threshold",
        _rule_low_hemoglobin,
        ["cbc", "anemia"],
    ),
    RuleDefinition(
        "high_cholesterol",
        "Total cholesterol above desirable range",
        _rule_high_cholesterol,
        ["lipid", "cardiovascular"],
    ),
    RuleDefinition(
        "high_ldl",
        "LDL cholesterol above safe range",
        _rule_high_ldl,
        ["lipid", "cardiovascular"],
    ),
    RuleDefinition(
        "high_blood_sugar",
        "Fasting blood glucose above normal range",
        _rule_high_blood_sugar,
        ["diabetes", "metabolic"],
    ),
    RuleDefinition(
        "high_hba1c",
        "HbA1c above normal — sustained high blood sugar",
        _rule_high_hba1c,
        ["diabetes", "metabolic"],
    ),
    RuleDefinition(
        "abnormal_tsh",
        "TSH outside normal thyroid range",
        _rule_abnormal_tsh,
        ["thyroid"],
    ),
    RuleDefinition(
        "low_vitamin_d",
        "Vitamin D below adequate level",
        _rule_low_vitamin_d,
        ["micronutrient"],
    ),
    RuleDefinition(
        "low_b12",
        "Vitamin B12 below adequate level",
        _rule_low_b12,
        ["micronutrient"],
    ),
    RuleDefinition(
        "high_creatinine",
        "Serum creatinine elevated — kidney function marker",
        _rule_high_creatinine,
        ["kidney"],
    ),
    RuleDefinition(
        "low_platelets",
        "Platelet count below normal (thrombocytopenia)",
        _rule_low_platelets,
        ["cbc", "bleeding"],
    ),
    RuleDefinition(
        "abnormal_wbc",
        "WBC count outside normal range",
        _rule_abnormal_wbc,
        ["cbc", "infection"],
    ),
    RuleDefinition(
        "missing_critical_tests",
        "No results found for critical test categories",
        _rule_missing_critical_tests,
        ["data_quality"],
    ),
]
