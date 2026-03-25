# Test Execution and Integration Documentation

## Overview
This document describes the automated test suite for Person 1 (Report Upload) and Person 3 (Wearable Ingestion) APIs.

## Test Files Created

### 1. **test_report_ingestion.py**
Tests Person 1's report upload and ingestion pipeline.

**Endpoint Tested:** `POST /reports/ingest`

**What it does:**
- Loads 3 pre-extracted medical reports (CBC, Lipid Panel, HbA1c)
- Formats them as `IngestReportRequest` objects
- POSTs each to the `/reports/ingest` endpoint
- Validates responses

**Sample Report Payload:**
```json
{
  "user_id": "pat-1",
  "report_id": "cbc-riya-2026",
  "report_type": "blood_test",
  "filename": "CBC_Report_Jan2026.pdf",
  "ocr_text": "COMPLETE BLOOD COUNT...",
  "extracted_data": {
    "hemoglobin": {"value": 9.8, "unit": "g/dL", "interpretation": "LOW"},
    "serum_iron": {"value": 42, "unit": "µg/dL", "interpretation": "LOW"},
    ...
  },
  "ai_insights": {
    "summary": "Low hemoglobin and iron levels indicate iron deficiency anaemia...",
    "risks": ["Fatigue", "Increased infection risk"],
    "recommendations": ["Iron-rich diet", "Follow-up CBC in 4 weeks"]
  }
}
```

### 2. **test_vitals_ingestion.py**
Tests Person 3's wearable vitals ingestion pipeline.

**Endpoint Tested:** `POST /api/v1/ingest/vitals`

**What it does:**
- Loads the pre-generated wearable payload (10k+ HR readings, 7 days sleep)
- Converts to `VitalReading` format
- POSTs batch vitals to the `/api/v1/ingest/vitals` endpoint
- Validates ingestion results

**Sample Vitals Payload:**
```json
{
  "user_id": "pat-1",
  "readings": [
    {
      "recorded_at": "2026-03-18T16:14:28Z",
      "metric_type": "heart_rate",
      "value": 80,
      "unit": "bpm",
      "device_id": "wearable_demo"
    },
    {
      "recorded_at": "2026-03-18T12:00:00Z",
      "metric_type": "sleep_hours",
      "value": 7.11,
      "unit": "hours",
      "device_id": "wearable_demo"
    },
    ...
  ]
}
```

### 3. **run_all_tests.py**
Integrated test runner that executes both test suites sequentially.

**Features:**
- Waits for backend server to be ready (30s timeout)
- Executes all tests with comprehensive logging
- Captures stdout/stderr
- Saves detailed results to `test_results.json`
- Provides summary with pass/fail statistics

**Usage:**
```bash
# Start backend first (in another terminal)
cd src && uvicorn backend.main:app --reload

# Then run tests
cd src/backend
python3 run_all_tests.py
```

## Test Data Files

### Generated Data (for Person 3 - Wearable)
- **wearable_payload.json** (1.1 MB)
  - 10,080 minute-by-minute heart rate readings (7 days)
  - 7 daily sleep sessions with stages and quality scores
  - Realistic physiological ranges for all metrics
  - Ready to POST directly to vitals ingestion API

### Extracted Reports (for Person 1 - OCR/Upload)
1. **extracted_cbc_report.json**
   - Hemoglobin: 9.8 g/dL (LOW)
   - Serum Iron: 42 µg/dL (LOW)
   - WBC, Platelets (normal)
   - AI Summary: Iron deficiency anaemia

2. **extracted_lipid_report.json**
   - Total Cholesterol: 210 mg/dL (HIGH)
   - LDL: 118 mg/dL (HIGH)
   - HDL: 48 mg/dL (NORMAL)
   - AI Summary: Dyslipidemia risk

3. **extracted_hba1c_report.json**
   - HbA1c: 7.8% (DIABETIC range)
   - Fasting Glucose: 142 mg/dL (HIGH)
   - AI Summary: Type 2 Diabetes confirmation

### UI Contracts
- **mock_doctor_roster.json**
  - 5 fake patients with alert severities
  - Alert counts and priority rankings
  - Last alert timestamps
  - Ready for doctor dashboard UI

- **mock_patient_detail.json**
  - Complete patient profile
  - Report history with extracted facts
  - Active alerts with severity levels
  - Environmental context (AQI, temperature, humidity)

## Expected Test Results

### When Backend is Running

**Person 1 (Reports) - Expected Output:**
```
✅ SUCCESS (3/3 reports)
   - CBC_Report_Jan2026.pdf: inserted with 6 extracted facts
   - Lipid_Panel_Jan2026.pdf: inserted with 6 extracted facts
   - HbA1c_Feb2026.pdf: inserted with 4 extracted facts
   Total extracted facts: 16
```

**Person 3 (Vitals) - Expected Output:**
```
✅ SUCCESS
   Inserted: 1014 readings
   Skipped: 0
   Total: 1014
   (10,080 HR readings limited to 1000 in batch, 14 sleep metrics)
```

## Running the Tests Locally

**Step 1: Install backend dependencies**
```bash
cd src/backend
pip install -r requirements.txt
```

**Step 2: Start the backend (Terminal 1)**
```bash
cd src
python -m uvicorn backend.main:app --reload
# Wait for: "Uvicorn running on http://0.0.0.0:8000"
```

**Step 3: Run tests (Terminal 2)**
```bash
cd src/backend
python3 run_all_tests.py
```

**Step 4: View results**
```bash
cat test_results.json
```

## Test Results File

All test results are saved to `test_results.json` with:
- Timestamp
- Backend server status
- Individual test outputs (stdout/stderr)
- Summary statistics
- Duration metrics

Example structure:
```json
{
  "timestamp": "2026-03-25T16:45:30.123456",
  "backend_ready": true,
  "tests": {
    "person_1_reports": {
      "status": "success",
      "return_code": 0,
      "duration": 2.34,
      "stdout": "..."
    },
    "person_3_vitals": {
      "status": "success",
      "return_code": 0,
      "duration": 1.56,
      "stdout": "..."
    }
  },
  "summary": {
    "person_1": "success",
    "person_3": "success",
    "overall_duration": 3.90
  }
}
```

## Integration Workflow

1. **Person 1 (Reports Team)** receives:
   - `test_report_ingestion.py` - test script
   - `extracted_cbc_report.json`, `extracted_lipid_report.json`, `extracted_hba1c_report.json` - test data
   - This covers: PDF upload → OCR → extraction → API ingest

2. **Person 3 (Wearable Team)** receives:
   - `test_vitals_ingestion.py` - test script
   - `wearable_payload.json` - generated test data
   - `generate_wearable_data.py` - script to regenerate with different parameters
   - This covers: wearable data ingestion API

3. **Person 4 (UI Team)** receives:
   - `mock_doctor_roster.json` - for doctor dashboard
   - `mock_patient_detail.json` - for patient detail view
   - Can mock-server these or integrate with mock data directly

4. **Integration Testing** (`run_all_tests.py`):
   - Validates end-to-end workflows
   - Documents all API interactions
   - Provides metrics and statistics

## Notes for Team

- All test data uses realistic medical values from public reference ranges
- Patient IDs follow the pattern: `pat-1`, `pat-2`, etc.
- All timestamps are in ISO 8601 format with UTC timezone
- The wearable payload is 1.1 MB (large but realistic)
- API request/response examples are included in docstrings
- Tests are idempotent: running multiple times is safe
