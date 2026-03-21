# Rules Engine Usage Guide

## Overview

The Vitalis rules engine is a **deterministic, zero-LLM alert generation system** that evaluates health data against 13 predefined medical rules. It reads structured lab results from the database, applies threshold-based logic, and produces actionable health alerts.

**Key Design Principles:**
- **Pure Functions**: All rules are side-effect-free and unit-testable without credentials
- **Idempotent**: Re-running evaluation replaces old alerts with fresh results
- **Evidence-Linked**: Every alert traces back to the specific lab results that triggered it
- **Zero AI Dependencies**: No LLMs required — all logic is hard-coded and auditable

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  POST /alerts/evaluate/{user_id}                                    │
│  ↓                                                                   │
│  backend/routes/alerts.py                                           │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  backend/rules/engine.py                                            │
│  • evaluate_rules(client, user_id)                                  │
│    ├─ Fetch medical_reports for user                                │
│    ├─ Fetch lab_results for those reports                           │
│    ├─ Convert to LabRow objects                                     │
│    └─ Run all 13 rules against LabRows                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  backend/rules/definitions.py                                       │
│  • ALL_RULES: List[RuleDefinition]                                  │
│    ├─ Rule 1:  any_abnormal                                         │
│    ├─ Rule 2:  low_hemoglobin                                       │
│    ├─ Rule 3:  high_cholesterol                                     │
│    ├─ ...                                                            │
│    └─ Rule 13: missing_critical_tests                               │
│                                                                      │
│  Each rule: (user_id, List[LabRow]) → AlertRecord                   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  backend/rules/inserter.py                                          │
│  • persist_alerts(client, user_id, alerts)                          │
│    ├─ Delete old alerts for user (idempotent)                       │
│    ├─ Insert triggered AlertRecords → alerts table                  │
│    └─ Insert evidence LabRows → alert_evidence table                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Module Structure

### `backend/rules/models.py`

Defines the core data models:

```python
class Severity(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

@dataclass
class AlertRecord:
    rule_id:   str
    triggered: bool
    severity:  Optional[Severity]
    reason:    Optional[str]
    evidence:  list  # List[LabRow]
```

### `backend/rules/definitions.py`

Contains all 13 rules as pure functions + helper data classes:

```python
@dataclass
class LabRow:
    """Lightweight value object representing a single lab result."""
    lab_result_id:   str
    report_id:       str
    test_name:       str
    value:           Optional[float]
    unit:            Optional[str]
    reference_range: Optional[str]
    abnormal_flag:   Optional[bool]
    report_date:     Optional[str]
    ocr_snippet:     Optional[str]

@dataclass
class RuleDefinition:
    rule_id:     str
    description: str
    func:        Callable[[str, List[LabRow]], AlertRecord]

ALL_RULES: List[RuleDefinition] = [...]  # 13 rules
```

### `backend/rules/engine.py`

Main evaluation logic:

```python
def evaluate_rules(client, user_id: str) -> List[AlertRecord]:
    """Evaluate all 13 rules against user's lab data.

    Returns only AlertRecords where triggered=True.
    """
    # 1. Fetch medical_reports for user
    # 2. Fetch lab_results for those reports
    # 3. Convert to LabRow objects
    # 4. Run each rule in ALL_RULES
    # 5. Return triggered alerts
```

### `backend/rules/inserter.py`

Database persistence:

```python
def persist_alerts(
    *,
    client,
    user_id: str,
    alerts: List[AlertRecord],
) -> Dict[str, Any]:
    """Delete old alerts and insert new ones (idempotent).

    Returns:
        {
            "deleted": int,
            "inserted": int,
            "evidence_inserted": int,
            "errors": List[str]
        }
    """
```

---

## The 13 Rules

### 1. `any_abnormal` — Abnormal Lab Values

**Trigger**: Any lab result has `abnormal_flag = True`

**Severity**:
- **HIGH**: ≥ 3 abnormal values
- **MEDIUM**: 1–2 abnormal values

**Example Alert**:
> "3 abnormal lab value(s) flagged: Hemoglobin, WBC, Platelet Count"

### 2. `low_hemoglobin` — Anemia Detection

**Trigger**: Hemoglobin < 12 g/dL

**Severity**:
- **HIGH**: < 8 g/dL (critically low)
- **MEDIUM**: 8–12 g/dL (mild anemia)

**Test Name Matching**: `hemoglobin`, `haemoglobin`, `hgb`, `hb` (excludes HbA1c)

**Example Alert**:
> "Low hemoglobin: 7.2 g/dL (normal ≥ 12 g/dL)"

### 3. `high_cholesterol` — Total Cholesterol

**Trigger**: Total cholesterol ≥ 200 mg/dL

**Severity**:
- **HIGH**: > 240 mg/dL
- **LOW**: 200–240 mg/dL (borderline)

**Test Name Matching**: `cholesterol` (excludes HDL, LDL, VLDL)

**Example Alert**:
> "High total cholesterol: 255 mg/dL (normal < 200)"

### 4. `high_ldl` — LDL Cholesterol

**Trigger**: LDL ≥ 160 mg/dL

**Severity**:
- **HIGH**: > 190 mg/dL
- **MEDIUM**: 160–190 mg/dL

**Test Name Matching**: `ldl`, `low density lipoprotein`

**Example Alert**:
> "Very high LDL cholesterol: 215 mg/dL (optimal < 100)"

### 5. `high_blood_sugar` — Glucose Monitoring

**Trigger**: Fasting blood glucose ≥ 100 mg/dL

**Severity**:
- **HIGH**: > 126 mg/dL (diabetic range)
- **MEDIUM**: 100–126 mg/dL (pre-diabetic)

**Test Name Matching**: `fasting blood glucose`, `fbs`, `blood glucose`, `blood sugar` (excludes urine glucose)

**Example Alert**:
> "Diabetic range fasting blood glucose: 145 mg/dL (normal < 100)"

### 6. `high_hba1c` — Long-term Glucose Control

**Trigger**: HbA1c ≥ 5.7%

**Severity**:
- **HIGH**: ≥ 6.5% (diabetic range)
- **MEDIUM**: 5.7–6.5% (pre-diabetic)

**Test Name Matching**: `hba1c`, `a1c`, `glycated hemoglobin`

**Example Alert**:
> "Pre-diabetic range HbA1c: 6.2% (normal < 5.7%)"

### 7. `abnormal_tsh` — Thyroid Function

**Trigger**: TSH < 0.4 or > 4.5 µIU/mL

**Severity**:
- **HIGH**: > 10 µIU/mL (severely elevated)
- **MEDIUM**: 0.4–4.5 range violated but not severe

**Test Name Matching**: `tsh`, `thyroid stimulating hormone`, `thyrotropin`

**Example Alert**:
> "Severely elevated TSH (hypothyroid): 12.3 µIU/mL (normal 0.4–4.5 µIU/mL)"

### 8. `low_vitamin_d` — Vitamin D Deficiency

**Trigger**: Vitamin D < 30 ng/mL

**Severity**:
- **HIGH**: < 12 ng/mL (severely deficient)
- **MEDIUM**: 12–30 ng/mL (insufficient)

**Test Name Matching**: `vitamin d`, `vit d`, `25(oh)`, `calcidiol`

**Example Alert**:
> "Severely deficient Vitamin D: 8.5 ng/mL (sufficient ≥ 30 ng/mL)"

### 9. `low_b12` — Vitamin B12 Deficiency

**Trigger**: B12 < 300 pg/mL

**Severity**:
- **HIGH**: < 150 pg/mL (severely low)
- **MEDIUM**: 150–300 pg/mL (low)

**Test Name Matching**: `vitamin b12`, `b12`, `cobalamin`

**Example Alert**:
> "Severely low Vitamin B12: 120 pg/mL (normal ≥ 300 pg/mL)"

### 10. `high_creatinine` — Kidney Function

**Trigger**: Serum creatinine ≥ 1.3 mg/dL

**Severity**:
- **HIGH**: > 2.0 mg/dL (severely elevated)
- **MEDIUM**: 1.3–2.0 mg/dL (elevated)

**Test Name Matching**: `creatinine` (excludes urine creatinine)

**Example Alert**:
> "Elevated serum creatinine: 1.7 mg/dL (normal < 1.2 mg/dL)"

### 11. `low_platelets` — Platelet Count

**Trigger**: Platelets < 150 ×10³/µL

**Severity**:
- **HIGH**: < 50 ×10³/µL (critically low)
- **MEDIUM**: 50–150 ×10³/µL (low)

**Test Name Matching**: `platelet`, `plt`

**Example Alert**:
> "Critically low platelet count: 42 ×10³/µL (normal 150–400 ×10³/µL)"

### 12. `abnormal_wbc` — White Blood Cell Count

**Trigger**: WBC < 2 or > 11 ×10³/µL

**Severity**:
- **HIGH**: > 15 or < 2 ×10³/µL (severely abnormal)
- **MEDIUM**: 2–11 range violated but not severe

**Test Name Matching**: `wbc`, `white blood cell`, `leucocyte`, `leukocyte`, `tlc`

**Example Alert**:
> "Elevated WBC count: 18.5 ×10³/µL (normal 4–11 ×10³/µL)"

### 13. `missing_critical_tests` — Coverage Check

**Trigger**: No CBC tests AND/OR no metabolic panel tests found

**Severity**: **LOW** (informational)

**Logic**:
- CBC keywords: `hemoglobin`, `wbc`, `platelet`, `rbc`
- Metabolic keywords: `glucose`, `hba1c`, `cholesterol`, `triglyceride`

**Example Alert**:
> "Missing critical test group(s): CBC (hemoglobin/WBC), metabolic panel (glucose/HbA1c/cholesterol)"

---

## API Usage

### Evaluate Rules and Persist Alerts

```bash
# Evaluate all 13 rules for a user
curl -X POST http://localhost:8000/alerts/evaluate/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "alerts_triggered": 3,
  "deleted": 2,
  "inserted": 3,
  "evidence_inserted": 5,
  "errors": []
}
```

### Retrieve Stored Alerts

```bash
# Get all alerts for a user (with evidence)
curl http://localhost:8000/alerts/550e8400-e29b-41d4-a716-446655440000
```

**Response**:
```json
{
  "user_id": "550e8400-...",
  "count": 2,
  "alerts": [
    {
      "id": "abc123-...",
      "severity": "high",
      "reason": "Low hemoglobin: 7.2 g/dL (normal ≥ 12 g/dL)",
      "created_at": "2026-03-21T10:30:00+00:00",
      "evidence": [
        {
          "id": "ev-001",
          "report_id": "report-abc",
          "lab_result_id": "lab-xyz",
          "ocr_text_snippet": "Hemoglobin  7.2  g/dL"
        }
      ]
    },
    {
      "id": "def456-...",
      "severity": "medium",
      "reason": "3 abnormal lab value(s) flagged: Hemoglobin, WBC, Glucose",
      "created_at": "2026-03-21T10:30:00+00:00",
      "evidence": [
        {"..."}
      ]
    }
  ]
}
```

---

## Programmatic Usage

### Example: Evaluate Rules Manually

```python
from backend.config.supabase_client import get_supabase_client
from backend.rules.engine import evaluate_rules
from backend.rules.inserter import persist_alerts

# Initialize
client = get_supabase_client()
user_id = "550e8400-e29b-41d4-a716-446655440000"

# Evaluate rules
alerts = evaluate_rules(client=client, user_id=user_id)

print(f"Triggered {len(alerts)} alerts:")
for alert in alerts:
    print(f"  [{alert.severity.value}] {alert.reason}")
    print(f"    Evidence: {len(alert.evidence)} lab result(s)")

# Persist to database
result = persist_alerts(client=client, user_id=user_id, alerts=alerts)
print(f"\nPersisted: {result['inserted']} alerts, {result['evidence_inserted']} evidence rows")
```

### Example: Implement a Custom Rule

```python
from backend.rules.definitions import LabRow, _trigger, _no_trigger
from backend.rules.models import AlertRecord, Severity

def _rule_low_iron(user_id: str, rows: List[LabRow]) -> AlertRecord:
    """Custom rule: flag low serum iron."""
    candidates = [r for r in rows if "iron" in r.test_name.lower() and r.value]
    if not candidates:
        return _no_trigger("low_iron")

    worst = min(candidates, key=lambda r: r.value)
    if worst.value >= 50:  # Normal: 50-150 µg/dL
        return _no_trigger("low_iron")

    severity = Severity.HIGH if worst.value < 30 else Severity.MEDIUM
    return _trigger(
        "low_iron",
        severity,
        f"Low serum iron: {worst.value} µg/dL (normal ≥ 50)",
        [worst]
    )

# Add to ALL_RULES in definitions.py to automatically evaluate it
```

---

## Testing

### Unit Tests (No Database Required)

The rules are pure functions, so you can test them with hand-crafted `LabRow` objects:

```python
from backend.rules.definitions import _rule_low_hemoglobin, LabRow
import uuid

# Create test data
rows = [
    LabRow(
        lab_result_id=str(uuid.uuid4()),
        report_id=str(uuid.uuid4()),
        test_name="Hemoglobin",
        value=7.2,
        unit="g/dL",
        abnormal_flag=True,
        ocr_snippet="Hemoglobin  7.2  g/dL"
    )
]

# Test rule
result = _rule_low_hemoglobin(user_id="test", rows=rows)
assert result.triggered == True
assert result.severity == Severity.HIGH
assert "7.2" in result.reason
print(f"✅ Test passed: {result.reason}")
```

### Integration Test (With Database)

```bash
cd src
PYTHONPATH=. python backend/scripts/alerts_test.py
```

This script:
1. Runs unit tests for all 13 rules (Part A)
2. Fetches real lab data from Supabase (Part B)
3. Evaluates rules against real data
4. Persists alerts
5. Verifies stored alerts in DB

**Configuration**: Edit `TEST_USER_ID` and `RUN_INTEGRATION` flag at top of script.

---

## Logging

The rules engine logs at multiple levels:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

**Log Output Examples**:

```
INFO:backend.rules.engine:Evaluating 13 rules against 42 lab rows for user_id=550e8400-...
INFO:backend.rules.engine:3/13 rules triggered for user_id=550e8400-...
WARNING:backend.rules.engine:Rule high_tsh raised an exception: division by zero
```

Enable DEBUG logging for detailed per-rule output:

```python
logging.getLogger("backend.rules").setLevel(logging.DEBUG)
```

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Rule evaluation time | < 100ms for 100 lab results |
| DB queries (per evaluation) | 2 (SELECT medical_reports, SELECT lab_results) |
| DB writes (per alert) | 1 INSERT (alerts) + N INSERTs (evidence) |
| Idempotency overhead | 1 DELETE query (removes old alerts) |

**Optimization Tip**: For batch processing, call `evaluate_rules()` once and cache `LabRow` objects if you need to test multiple rule sets.

---

## Common Issues

### No Alerts Triggered (Expected Some)

1. **Check user has lab results**:
   ```sql
   SELECT COUNT(*) FROM lab_results lr
   JOIN medical_reports mr ON lr.report_id = mr.id
   WHERE mr.user_id = '<uuid>';
   ```

2. **Check lab values are numeric**:
   Rules skip rows where `value is None`. Ensure Gemini extraction produced numeric values.

3. **Check test name matching**:
   Rules use fuzzy keyword matching. If test name is `"Hb (Hemoglobin)"`, it will match. But `"Iron Binding Capacity"` won't match the hemoglobin rule.

### Alert Evidence is Empty

This is expected for `missing_critical_tests` rule, which doesn't cite specific lab results. All other rules should populate `evidence`.

### Idempotency: Old Alerts Not Deleted

Check that `alert_evidence` table has `ON DELETE CASCADE` constraint on `alert_id`:

```sql
ALTER TABLE alert_evidence
  ADD CONSTRAINT fk_alert_id
  FOREIGN KEY (alert_id) REFERENCES alerts(id)
  ON DELETE CASCADE;
```

---

## Extending the System

### Adding a New Rule

1. **Define the rule function** in `backend/rules/definitions.py`:
   ```python
   def _rule_my_custom_rule(user_id: str, rows: List[LabRow]) -> AlertRecord:
       # Your logic here
       return _trigger("my_custom_rule", Severity.MEDIUM, "...", [...])
   ```

2. **Add to ALL_RULES**:
   ```python
   ALL_RULES.append(
       RuleDefinition("my_custom_rule", "Description", _rule_my_custom_rule)
   )
   ```

3. **Test it**:
   ```python
   # In alerts_test.py, add to Part A fixtures
   ```

### Changing Thresholds

Edit the hardcoded values in `definitions.py`. For example, to change hemoglobin threshold from 12 → 11:

```python
# Line 130 in definitions.py
if val >= 11.0:  # was 12.0
    return _no_trigger("low_hemoglobin")
```

**Pro Tip**: For dynamic thresholds (e.g., age/gender-specific), store them in a new `rule_config` table and fetch them in `evaluate_rules()`.

---

## FAQ

**Q: Can I run rules on-demand without persisting to DB?**

Yes:
```python
from backend.rules.engine import evaluate_rules
alerts = evaluate_rules(client, user_id)
# Don't call persist_alerts()
```

**Q: How do I get alerts for a specific rule only?**

Filter after evaluation:
```python
alerts = evaluate_rules(client, user_id)
hb_alerts = [a for a in alerts if a.rule_id == "low_hemoglobin"]
```

**Q: Can rules access external data (weather, medication history)?**

Not directly. Rules are pure functions that only receive `LabRow` objects. To incorporate external data:
1. Add fields to `LabRow` (e.g., `weather_aqi`)
2. Populate those fields in `engine.py` `_build_lab_rows()`
3. Use them in rule logic

**Q: How do I disable a specific rule?**

Remove it from `ALL_RULES` in `definitions.py`, or filter it out in the API route:

```python
# In routes/alerts.py, before calling persist_alerts():
alerts = [a for a in alerts if a.rule_id != "missing_critical_tests"]
```

---

## Summary

The Vitalis rules engine provides:
- ✅ **13 evidence-based health alert rules**
- ✅ **Pure, testable, side-effect-free functions**
- ✅ **Idempotent database persistence**
- ✅ **Comprehensive test coverage (unit + integration)**
- ✅ **Zero LLM dependencies**
- ✅ **Full audit trail via evidence linking**

For implementation details, see:
- **Module code**: `src/backend/rules/`
- **API routes**: `src/backend/routes/alerts.py`
- **Test script**: `src/backend/scripts/alerts_test.py`
- **Week 2 README**: `src/README1.md`
