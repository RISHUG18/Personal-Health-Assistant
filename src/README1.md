# Week 2 — Structured Extraction & Database Ingestion

## Overview

This module turns raw PDF/image medical lab reports into **structured rows** in the database.  
The pipeline is fully automatic: uploading a report triggers OCR and Gemini AI extraction without any further client action.

Two ingestion modes are provided:

| Mode | Endpoint | Behaviour |
|------|----------|-----------|
| **Async (recommended)** | `POST /reports/ingest` | Returns HTTP 202 immediately with a `report_id`; OCR + Gemini run in the background |
| **Synchronous** | `POST /reports/process` | Waits for the full pipeline before responding; convenient for scripts |

---

## Architecture

```
PDF / Image
     │
     ▼
┌──────────────────────────┐
│  Upload to Supabase       │  ← runs synchronously, returns report_id
│  Storage + pending row    │  POST /reports/ingest  (202 Accepted)
└──────────┬───────────────┘
           │  background task (async, per-client)
           ▼
┌──────────────────────────┐
│  Tesseract OCR            │
│  preprocessor →           │  processing_status: pending → ocr_complete
│  ocr_engine               │
│  → medical_reports        │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Gemini AI Extraction     │  processing_status: ocr_complete → done
│  → lab_results            │  POST /reports/extract-labs-gemini
└──────────────────────────┘

Poll progress: GET /reports/status/{report_id}
```

### Alerts pipeline (separate, on-demand)

```
lab_results (from above)
     │
     ▼
POST /alerts/evaluate/{user_id}
     │  13 deterministic rules evaluated
     ▼
alerts + alert_evidence (Supabase)
     │
     ▼
GET /alerts/{user_id}
```

---

## Backend Folder Structure

```
backend/
├── main.py                      # FastAPI app entrypoint
├── requirements.txt             # Python dependencies
├── verify_reports.py            # End-to-end verification script
│
├── config/
│   └── supabase_client.py       # Supabase client + env helpers
│
├── controllers/
│   └── reports_controller.py    # Business logic (upload, OCR, pipeline)
│
├── routes/
│   ├── reports.py               # HTTP routes for report ingestion
│   ├── alerts.py                # HTTP routes for alerts (fetch + evaluate)
│   └── rag.py                   # RAG query pipeline routes
│
├── ocr/                         # OCR module
│   ├── preprocessor.py          # Grayscale → Non-Local Means denoise → deskew
│   ├── ocr_engine.py            # Tesseract OCR wrapper → (text, confidence)
│   ├── pipeline.py              # Legacy regex extraction (not used by main pipeline)
│   └── README.md
│
├── extraction/                  # Gemini AI extraction module
│   ├── gemini_extractor.py      # Gemini API call + 3× retry with back-off
│   ├── models.py                # Pydantic models for extraction response
│   ├── normalizer.py            # Unit/date normalization
│   ├── inserter.py              # Idempotent DB insertion into lab_results
│   └── pipeline.py              # process_report_with_gemini() orchestrator
│
├── rules/                       # Deterministic health rules engine
│   ├── definitions.py           # 13 rule functions (low Hb, high cholesterol, …)
│   ├── engine.py                # evaluate_rules(client, user_id) → List[AlertRecord]
│   ├── inserter.py              # persist_alerts() → idempotent DB write
│   └── models.py                # AlertRecord, RuleResult, Severity, EvidenceRef
│
├── services/                    # Shared services
│   ├── context/                 # Context builder for RAG
│   ├── embeddings/              # Embedding interfaces + SentenceTransformers
│   ├── preprocessing/           # Text cleaning & chunking
│   └── retrieval/               # Vector retrieval (pgvector, FAISS, mock)
│
├── prompts/                     # System prompts for LLM roles
├── scripts/                     # Developer utility scripts (not imported by production)
└── tests/                       # Unit test suite
```

---

## Setup

### 1. Environment Variables

Create a `.env` file in `src/backend/`:

```env
# Supabase (required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_REPORTS_BUCKET=medical-reports
SUPABASE_OCR_REPORTS_TABLE=medical_reports

# Gemini AI (required for extraction)
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.1-pro-preview   # default if unset
```

### 2. System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler
```

### 3. Python Dependencies

```bash
cd src
pip install -r backend/requirements.txt
```

### 4. Database Setup

Run in your Supabase SQL editor in order:

```sql
-- 1. Base schema (tables: medical_reports, lab_results, alerts, alert_evidence)
--    Run: db/schema.sql

-- 2. RAG chunks
--    Run: db/migrations/001_add_report_chunks.sql

-- 3. Chunk metadata
--    Run: db/migrations/002_add_report_chunk_metadata.sql

-- 4. Async pipeline status tracking (makes ocr_text nullable, adds processing_status)
--    Run: db/migrations/003_add_processing_status.sql
```

### 5. Start the Server

```bash
cd src
PYTHONPATH=. uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

---

## API Endpoints

### Authentication

**`POST /auth/register`**

Register a new user in Supabase Auth and instantly mirror the profile into the `public.users` table. 
The backend actively bypasses standard required email confirmations via Supabase Admin APIs so you receive a valid JWT token immediately. 
Includes atomic rollback mechanisms: if the public table mapping fails (e.g., from DB constraints), the Auth footprint is deleted so the user isn't indefinitely locked out from retrying.

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePassword123!", "full_name": "Test User", "role": "patient"}'
```

Returns `201 Created`:
```json
{
  "message": "User registered successfully",
  "user_id": "a1b2c3d4-...",
  "access_token": "eyJhbGciOiJFUzI1NiIs...",
  "refresh_token": "..."
}
```

---

**`POST /auth/login`**

Authenticate using Supabase and retrieve active JWT tokens. Additionally updates `last_login_at` automatically in the `users` table.

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePassword123!"}'
```

---

### Secure Upload Pipeline

**`POST /upload/report`**

A completely protected endpoint demanding a valid JWT `Bearer` token. It cleanly uploads medical PDFs directly to the `medical-reports` Supabase storage bucket while preserving RLS separation schemas using isolated service clients. 
*Note: Unauthenticated or invalid token requests are strictly rejected with 401/403.*

```bash
curl -X POST http://localhost:8000/upload/report \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>" \
  -F "file=@/path/to/report.pdf"
```

---

### Reports — Full Async Pipeline (Recommended)

**`POST /reports/ingest`**

Upload a PDF or image. OCR and Gemini extraction start automatically in the background.  
Returns **HTTP 202** immediately — the client does not wait for processing to finish.

```bash
curl -X POST http://localhost:8000/reports/ingest \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
```

Response:
```json
{
  "report_id": "a1b2c3d4-...",
  "storage_path": "550e8400-.../20260309T120000Z_abc_report.pdf",
  "public_url": "https://...",
  "processing_status": "pending",
  "message": "Report queued. Poll GET /reports/status/{report_id} for progress."
}
```

Pipeline stages stored in `medical_reports.processing_status`:

| Stage | Meaning |
|-------|---------|
| `pending` | Uploaded; OCR not yet started |
| `ocr_complete` | OCR text saved; Gemini extraction running |
| `done` | Lab results written to `lab_results` |
| `failed` | Error — see `processing_error` field |

---

**`GET /reports`**

List all uploaded medical reports for the authenticated user, sorted from newest to oldest. Supports pagination via query parameters.

```bash
curl "http://localhost:8000/reports?limit=10&offset=0" \
  -H "Authorization: Bearer <JWT_ACCESS_TOKEN>"
```

Response:
```json
{
  "items": [
    {
      "id": "a1b2c3d4-...",
      "created_at": "2026-03-09T12:00:00+00:00",
      "source_file_name": "report.pdf",
      "report_date": "2026-01-15",
      "report_type": "Laboratory Investigation Report",
      "processing_status": "done",
      "processing_error": null
    }
  ],
  "total": 4,
  "limit": 10,
  "offset": 0
}
```

---

**`GET /reports/status/{report_id}`**

Poll progress after calling `/ingest`.

```bash
curl http://localhost:8000/reports/status/a1b2c3d4-...
```

Response (while processing):
```json
{
  "report_id": "a1b2c3d4-...",
  "source_file_name": "report.pdf",
  "processing_status": "ocr_complete",
  "processing_error": null,
  "ocr_confidence": 94.3,
  "lab_results_count": null
}
```

Response (when done):
```json
{
  "report_id": "a1b2c3d4-...",
  "processing_status": "done",
  "ocr_confidence": 94.3,
  "lab_results_count": 14
}
```

---

### Reports — Synchronous Pipeline (Scripts / Testing)

**`POST /reports/process`**

Same pipeline (upload → OCR → Gemini), but blocks until fully complete. Gemini is **always** used — there is no regex fallback.

```bash
curl -X POST http://localhost:8000/reports/process \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
```

Response (on success):
```json
{
  "report_id": "...",
  "storage_path": "...",
  "public_url": "...",
  "processing_status": "done",
  "ocr_confidence": 92.1,
  "ocr_text_preview": "...",
  "gemini_extraction": { "inserted": 12, "skipped": 0 },
  "gemini_error": null
}
```

---

### Reports — Low-Level Step Endpoints

Use these when you need fine-grained control or want to retry a single stage.

| Endpoint | Purpose |
|----------|---------|
| `POST /reports/upload` | Upload to Supabase Storage only — no OCR, no DB row |
| `POST /reports/ocr` | Run OCR on an already-uploaded file and persist to `medical_reports` |
| `POST /reports/extract-labs-gemini` | Run Gemini extraction on a report that already has OCR text |

```bash
# Step 1 — Upload only
curl -X POST http://localhost:8000/reports/upload \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@/path/to/report.pdf"
# → {"path": "...", "public_url": "..."}

# Step 2 — OCR
curl -X POST http://localhost:8000/reports/ocr \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "storage_path=<path from step 1>"
# → {"report_id": "...", "ocr_text": "...", "confidence": 92.5}

# Step 3 — Gemini extraction
curl -X POST http://localhost:8000/reports/extract-labs-gemini \
  -F "report_id=<report_id from step 2>"
# → {"inserted": 12, "skipped": 0, "extraction_log": {...}}
```

---

### Alerts

**`POST /alerts/evaluate/{user_id}`**

Run the deterministic rules engine for a user. Fetches their lab results, evaluates 13 health rules, and persists the results to the `alerts` and `alert_evidence` tables.  
The operation is **idempotent** — re-running replaces any previous alerts.

```bash
curl -X POST http://localhost:8000/alerts/evaluate/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "user_id": "550e8400-...",
  "alerts_triggered": 3,
  "deleted": 2,
  "inserted": 3,
  "evidence_inserted": 5,
  "errors": []
}
```

---

**`GET /alerts/{user_id}`**

Fetch all stored alerts for a user from the database, including the evidence that triggered each one.

```bash
# With evidence (default)
curl http://localhost:8000/alerts/550e8400-e29b-41d4-a716-446655440000

# Without evidence
curl "http://localhost:8000/alerts/550e8400-e29b-41d4-a716-446655440000?include_evidence=false"
```

Response:
```json
{
  "user_id": "550e8400-...",
  "count": 2,
  "alerts": [
    {
      "id": "...",
      "severity": "high",
      "reason": "Hemoglobin 7.2 g/dL — critically low (< 8 g/dL)",
      "created_at": "2026-03-09T12:00:00+00:00",
      "evidence": [
        {
          "id": "...",
          "report_id": "...",
          "lab_result_id": "...",
          "ocr_text_snippet": "Hemoglobin  7.2  g/dL"
        }
      ]
    },
    {
      "id": "...",
      "severity": "medium",
      "reason": "Total Cholesterol 215 mg/dL — borderline high (200–240)",
      "created_at": "2026-03-09T12:00:00+00:00",
      "evidence": [...]
    }
  ]
}
```

Severity values: `"low"` | `"medium"` | `"high"`

---

## OCR Module (`ocr/`)

### Preprocessing Pipeline

```
Image → grayscale → fastNlMeansDenoising (Non-Local Means) → adaptive threshold → deskew
```

| File | Key Function | Description |
|------|-------------|-------------|
| `preprocessor.py` | `preprocess_image(img)` | Full image preprocessing chain |
| `ocr_engine.py` | `run_ocr(img)` | Tesseract OCR → `(text, confidence)` |

---

## Gemini Extraction (`extraction/`)

### How It Works

1. **Fetch OCR text** — reads `ocr_text` from the `medical_reports` row
2. **Prompt Gemini** — structured prompt with strict rules: preserve exact values, extract every test, `null` for uncertainty, no interpretation
3. **Model**: `gemini-3.1-pro-preview` (configurable via `GEMINI_MODEL` env var)
4. **Retry logic**: same model, up to 3 attempts, exponential back-off (`2s → 4s → 8s`). No multi-model fallback.
5. **Normalize** — units to canonical forms, dates to ISO-8601
6. **Idempotent insert** — deletes previous `lab_results` for the report before inserting fresh rows

---

## Rules Engine (`rules/`) — ✅ FULLY IMPLEMENTED

The rules engine is a **deterministic, zero-LLM alert generation system** that provides automated health monitoring without relying on AI interpretation.

### Architecture

```
backend/rules/
├── models.py        # Data models: Severity, AlertRecord
├── definitions.py   # All 13 rule functions + LabRow model (pure, testable)
├── engine.py        # evaluate_rules() — fetches data & orchestrates evaluation
└── inserter.py      # persist_alerts() — idempotent DB persistence
```

### Key Features

✅ **Pure Functions**: All rules are side-effect-free, no DB access inside rule logic
✅ **Idempotent**: Re-running evaluation replaces old alerts completely
✅ **Evidence-Linked**: Every alert traces back to the specific lab results that triggered it
✅ **Zero AI Dependencies**: No LLMs — all logic is hard-coded and auditable
✅ **Unit Testable**: Full test coverage without requiring credentials or database
✅ **Comprehensive Logging**: DEBUG/INFO/WARNING logs for troubleshooting

### The 13 Rules

| Rule ID | What it checks | Severity Levels |
|---------|----------------|-----------------|
| `any_abnormal` | Any lab value flagged as abnormal | HIGH (≥3), MEDIUM (1-2) |
| `low_hemoglobin` | Hemoglobin < 12 g/dL | HIGH (<8), MEDIUM (8-12) |
| `high_cholesterol` | Total cholesterol ≥ 200 mg/dL | HIGH (>240), LOW (200-240) |
| `high_ldl` | LDL ≥ 160 mg/dL | HIGH (>190), MEDIUM (160-190) |
| `high_blood_sugar` | Fasting glucose ≥ 100 mg/dL | HIGH (>126), MEDIUM (100-126) |
| `high_hba1c` | HbA1c ≥ 5.7% | HIGH (≥6.5), MEDIUM (5.7-6.5) |
| `abnormal_tsh` | TSH < 0.4 or > 4.5 µIU/mL | HIGH (>10), MEDIUM (other) |
| `low_vitamin_d` | Vitamin D < 30 ng/mL | HIGH (<12), MEDIUM (12-30) |
| `low_b12` | Vitamin B12 < 300 pg/mL | HIGH (<150), MEDIUM (150-300) |
| `high_creatinine` | Serum creatinine ≥ 1.3 mg/dL | HIGH (>2.0), MEDIUM (1.3-2.0) |
| `low_platelets` | Platelet count < 150 ×10³/µL | HIGH (<50), MEDIUM (50-150) |
| `abnormal_wbc` | WBC < 2 or > 11 ×10³/µL | HIGH (<2 or >15), MEDIUM (other) |
| `missing_critical_tests` | Missing CBC and/or metabolic panel | LOW (informational) |

### Environment-Aware Rules Extensions

The rules engine now optionally supports **environmental modifiers** derived from the `environmental_data` table. If the deterministic threshold evaluates to `True`, the engine further checks environmental constraints. When conditions are met, alert severities are systematically escalated (never skipping a tier) and reasoning strings are updated with contextual evidence inserted into the database.

| Environmental Trigger | Tests Affected | Modifier | Thresholds Used |
|-----------------------|----------------|----------|-----------------|
| **Poor Air Quality** | `abnormal_wbc`, `low_hemoglobin` | Bump Severity +1 | AQI > 100 |
| **High Temperature** | `abnormal_tsh`, `low_vitamin_d` | Bump Severity +1 | Temperature > 30°C |
| **Extreme Weather** | `any_abnormal`, `low_b12` | Append Advisory to Reason | AQI > 150 OR Temperature > 35°C |

*These modifications safely output `environmental_evidence` in a JSON block saved perfectly into the `alert_evidence` schema format alongside standard testing.*

### Test Name Matching Examples

Rules use **fuzzy keyword matching** to identify test types across different lab report formats:

- **Hemoglobin**: `"Hemoglobin"`, `"Haemoglobin"`, `"Hgb"`, `"HB"` (excludes HbA1c)
- **Total Cholesterol**: `"Total Cholesterol"`, `"Cholesterol"` (excludes HDL/LDL/VLDL)
- **Glucose**: `"Fasting Blood Glucose"`, `"FBS"`, `"FBG"`, `"Blood Sugar"` (excludes urine)
- **TSH**: `"TSH"`, `"Thyroid Stimulating Hormone"`, `"Thyrotropin"`
- **WBC**: `"WBC"`, `"White Blood Cell"`, `"Leucocyte"`, `"Leukocyte"`, `"TLC"`

### Data Models

```python
# backend/rules/definitions.py
@dataclass
class LabRow:
    """Lightweight value object passed to every rule function."""
    lab_result_id:   str
    report_id:       str
    test_name:       str
    value:           Optional[float]      # None for non-numeric results
    unit:            Optional[str]
    reference_range: Optional[str]
    abnormal_flag:   Optional[bool]
    report_date:     Optional[str]
    ocr_snippet:     Optional[str]        # Raw OCR text for evidence

# backend/rules/models.py
class Severity(Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

@dataclass
class AlertRecord:
    """Result of evaluating a single rule."""
    rule_id:   str
    triggered: bool
    severity:  Optional[Severity]
    reason:    Optional[str]       # Human-readable alert message
    evidence:  list                # List[LabRow] that triggered this alert
```

### Core Functions

**1. Evaluate Rules** (`backend/rules/engine.py`):

```python
def evaluate_rules(client, user_id: str) -> List[AlertRecord]:
    """Evaluate all 13 rules against user's lab data.

    Steps:
    1. Fetch medical_reports for user_id
    2. Fetch lab_results for those reports
    3. Convert DB rows to LabRow objects
    4. Run each rule function in ALL_RULES
    5. Return only triggered alerts

    Returns:
        List of AlertRecord where triggered=True
    """
```

**2. Persist Alerts** (`backend/rules/inserter.py`):

```python
def persist_alerts(
    *,
    client,
    user_id: str,
    alerts: List[AlertRecord],
) -> Dict[str, Any]:
    """Delete old alerts and insert new ones (idempotent).

    The operation is atomic per user:
    1. DELETE all existing alerts for user_id (CASCADE removes evidence)
    2. INSERT new alert rows
    3. INSERT evidence rows linking to lab_results

    Returns:
        {
            "deleted": int,          # Old alerts removed
            "inserted": int,          # New alerts written
            "evidence_inserted": int, # Evidence rows written
            "errors": List[str]       # Any errors encountered
        }
    """
```

### Example Rule Implementation

```python
# backend/rules/definitions.py

def _rule_low_hemoglobin(user_id: str, rows: List[LabRow]) -> AlertRecord:
    """Rule 2: Detect anemia (low hemoglobin)."""

    # 1. Filter to hemoglobin tests (fuzzy matching, exclude HbA1c)
    candidates = [r for r in rows if _is_hemoglobin(r) and r.value is not None]
    if not candidates:
        return _no_trigger("low_hemoglobin")

    # 2. Find the lowest value
    worst = min(candidates, key=lambda r: r.value)
    val = worst.value

    # 3. Check threshold
    if val >= 12.0:
        return _no_trigger("low_hemoglobin")

    # 4. Determine severity (critical < 8, mild < 12)
    severity = Severity.HIGH if val < 8.0 else Severity.MEDIUM

    # 5. Generate human-readable reason
    unit = worst.unit or "g/dL"
    reason = f"Low hemoglobin: {val} {unit} (normal ≥ 12 g/dL)"

    # 6. Return alert with evidence (the LabRow that triggered it)
    return _trigger("low_hemoglobin", severity, reason, [worst])
```

### Logging

The rules engine logs at multiple levels:

```python
# INFO: high-level progress
INFO:backend.rules.engine:Evaluating 13 rules against 42 lab rows for user_id=550e8400-...
INFO:backend.rules.engine:3/13 rules triggered for user_id=550e8400-...

# WARNING: exceptions during rule evaluation
WARNING:backend.rules.engine:Rule high_tsh raised an exception: division by zero
```

Enable DEBUG for detailed per-rule output:
```python
import logging
logging.getLogger("backend.rules").setLevel(logging.DEBUG)
```

### Testing Strategy

**Unit Tests** (no database or API keys required):

```bash
cd src
PYTHONPATH=. python backend/scripts/alerts_test.py
```

**Part A — Pure Function Tests**:
- Tests all 13 rules with hand-crafted `LabRow` fixtures
- Validates both "should fire" and "should NOT fire" branches
- Verifies severity escalation (e.g., critically low Hb → HIGH, mildly low → MEDIUM)
- Confirms rules are pure and isolated (no side effects)

**Part B — Integration Test** (requires Supabase):
- Fetches real lab data from `lab_results` table
- Evaluates all 13 rules against actual patient data
- Persists alerts to `alerts` + `alert_evidence` tables
- Re-queries database and verifies stored alerts

Configuration: Edit `TEST_USER_ID` at top of `alerts_test.py`.

### Performance Characteristics

| Metric | Value |
|--------|-------|
| Rule evaluation time | < 100ms for 100 lab results |
| DB queries (per evaluation) | 2 SELECT (medical_reports + lab_results) |
| DB writes (per alert) | 1 INSERT (alerts) + N INSERTs (evidence) |
| Idempotency overhead | 1 DELETE query (removes old alerts) |
| Memory footprint | ~1KB per LabRow object |

### Extension Points

**Adding a New Rule**:

1. Define the rule function in `backend/rules/definitions.py`:
   ```python
   def _rule_my_custom_rule(user_id: str, rows: List[LabRow]) -> AlertRecord:
       candidates = [r for r in rows if "iron" in r.test_name.lower()]
       # Your logic here...
       return _trigger("my_custom_rule", Severity.MEDIUM, "...", [...])
   ```

2. Add to `ALL_RULES` list:
   ```python
   ALL_RULES.append(
       RuleDefinition("my_custom_rule", "Description", _rule_my_custom_rule)
   )
   ```

3. Write unit tests in `alerts_test.py` Part A

**Changing Thresholds**:
- Edit hardcoded values in `definitions.py` (e.g., change hemoglobin from 12 → 11)
- For dynamic/personalized thresholds (age/gender-specific), create a `rule_config` table

**Adding External Data**:
- Rules only receive `LabRow` objects (pure functions)
- To incorporate weather/medication/etc., add fields to `LabRow` and populate in `engine.py`

### Common Issues & Troubleshooting

**1. No alerts triggered (expected some)**:
- Check that user has `lab_results` rows:
  ```sql
  SELECT COUNT(*) FROM lab_results lr
  JOIN medical_reports mr ON lr.report_id = mr.id
  WHERE mr.user_id = '<uuid>';
  ```
- Verify lab values are numeric (rules skip rows where `value is None`)
- Check test name matching (rules use fuzzy keywords; add to `_KEYWORDS` sets if needed)

**2. Alert evidence is empty**:
- Expected for `missing_critical_tests` rule (no specific lab results to cite)
- All other rules should populate `evidence` list

**3. Old alerts not deleted (idempotency broken)**:
- Verify `alert_evidence` table has `ON DELETE CASCADE` constraint:
  ```sql
  ALTER TABLE alert_evidence
    ADD CONSTRAINT fk_alert_id
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
    ON DELETE CASCADE;
  ```

**4. Rule raised exception**:
- Check logs for WARNING messages
- Common causes: division by zero, unexpected `None` values
- Rules should handle edge cases gracefully (wrap in try/except if needed)

### Comprehensive Documentation

For detailed usage examples, API integration, and advanced scenarios, see:

📖 **[Rules Engine Usage Guide](../../docs/RULES_ENGINE_GUIDE.md)**

This guide includes:
- Detailed rule-by-rule documentation with examples
- Programmatic usage patterns
- Custom rule implementation tutorial
- FAQ and troubleshooting
- Performance optimization tips

---

## Database Tables

### `medical_reports`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Report owner |
| `report_date` | DATE | Date of report (set by Gemini extraction) |
| `report_type` | TEXT | Report type (set by Gemini extraction) |
| `source_file_name` | TEXT | Original filename |
| `source_url` | TEXT | Supabase Storage URL |
| `ocr_text` | TEXT | Full OCR output (nullable until OCR completes) |
| `ocr_engine` | TEXT | `tesseract` |
| `ocr_confidence` | NUMERIC | Average Tesseract confidence (%) |
| `processing_status` | TEXT | `pending \| ocr_complete \| done \| failed` |
| `processing_error` | TEXT | Error message if `processing_status = 'failed'` |

### `lab_results`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `report_id` | UUID | FK → `medical_reports.id` |
| `test_name` | TEXT | Lab test name |
| `value` | NUMERIC | Numeric result (NULL if non-numeric) |
| `unit` | TEXT | Measurement unit |
| `reference_range` | TEXT | Normal range as printed |
| `abnormal_flag` | BOOLEAN | True if outside reference range |
| `extracted_from_page` | INT | Source page number |

> **Note:** `lab_results` has no `user_id`. To query lab results for a user:  
> `SELECT lr.* FROM lab_results lr JOIN medical_reports mr ON lr.report_id = mr.id WHERE mr.user_id = '<uuid>'`

### `alerts`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | Alert owner |
| `severity` | TEXT | `low \| medium \| high` |
| `reason` | TEXT | Human-readable explanation |
| `created_at` | TIMESTAMP | When the alert was generated |

### `alert_evidence`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `alert_id` | UUID | FK → `alerts.id` |
| `report_id` | UUID | FK → `medical_reports.id` |
| `lab_result_id` | UUID | FK → `lab_results.id` |
| `ocr_text_snippet` | TEXT | Raw text excerpt that triggered the alert |

---

## Key Design Decisions

1. **Async-first ingestion**: `POST /reports/ingest` returns a `report_id` immediately with HTTP 202. OCR and Gemini extraction run as a FastAPI `BackgroundTask` so multiple clients are processed in parallel.

2. **Gemini is the only extraction path**: The regex extraction endpoint (`/extract-labs`) has been removed. All lab data comes from Gemini AI.

3. **Idempotent operations**: Re-submitting a report or re-evaluating alerts always produces a clean slate — old rows are deleted before new ones are inserted.

4. **OCR text is immutable**: `medical_reports.ocr_text` is set exactly once by Tesseract and never modified. All downstream operations (Gemini, RAG indexing) read from it.

5. **Rules are pure**: Alert rules in `backend/rules/definitions.py` take only a user ID and a list of `LabRow` objects — no database access inside the rule functions. This makes them fully unit-testable without credentials.

6. **Status polling over webhooks**: Pipeline status is tracked as a column in `medical_reports` so the client can poll `GET /reports/status/{report_id}` without any additional infrastructure.

---

## Verification Scripts

Run from `src/`:

```bash
# OCR + Gemini full pipeline (end-to-end)
PYTHONPATH=. python backend/verify_reports.py

# Alerts rules engine (unit tests + DB integration)
PYTHONPATH=. python backend/scripts/alerts_test.py
```
