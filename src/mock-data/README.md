# Mock Data for Healthcare Platform Tests

> Complete mock data package for testing the HealthCompanion platform. Unblocks all three development teams (UI, Wearable API, Report Pipeline).

---

## 📦 What's Included

This folder contains production-ready mock data and generators for testing three critical system components:

| Team | File(s) | Purpose |
|------|---------|---------|
| **Person 4** (UI Frontend) | `mock_doctor_roster.json`<br/>`mock_patient_detail.json` | Exact JSON contracts for dashboard components |
| **Person 3** (Wearable API) | `generate_wearable_data.js`<br/>`wearable_payload.json` | 7-day realistic wearable data generator |
| **Person 1** (Report Pipeline) | `generate_test_pdfs.js`<br/>`mock_report_extractions.json`<br/>`test-pdfs/` | PDF generation + reference extractions |

---

## 🚀 Quick Start by Team

### Person 4 — UI Frontend Development

**What you need:** Exact data contracts for your React components.

```bash
# Copy mock data into your project
cp mock_doctor_roster.json src/data/
cp mock_patient_detail.json src/data/

# In your React component:
import roster from '@/data/mock_doctor_roster.json';
import detail from '@/data/mock_patient_detail.json';

// Use directly in components
export function DoctorDashboard() {
  return roster.patientsUnderCare.map(patient => (
    <PatientCard key={patient.patientId} patient={patient} />
  ));
}
```

**Data Structure:**
- **mock_doctor_roster.json** — 5 patients with alert badges
  - Patient names, IDs, conditions, health metrics
  - Alert counts and severity levels (high/medium/low)
  - Recent reports with status (processed/pending)
  
- **mock_patient_detail.json** — Full patient view
  - Complete medical history, current medications
  - 2 sample lab reports with extracted data
  - AI-generated summaries with confidence scores
  - 7-day health metrics trends
  - Environment AQI context data

**Test Coverage:**
- ✅ 5 diverse patient profiles
- ✅ 8 total alerts across all patients
- ✅ Multiple severity levels for testing UI states
- ✅ Realistic health metrics (not random)

---

### Person 3 — Wearable Data API

**What you need:** Test payload with realistic wearable data.

```bash
# Generate 7 days of wearable data
node generate_wearable_data.js

# Output: wearable_payload.json (13,183 data points)
# Contains: minute-by-minute heart rate + sleep stages

# Test your API ingestion
curl -X POST http://localhost:5000/api/wearable/ingest \
  -H "Content-Type: application/json" \
  -d @wearable_payload.json

# Expected response: 201 Created, 13,183 points ingested
```

**Data Characteristics:**
- **Duration:** 7 consecutive days (10,080 minutes)
- **Granularity:** Minute-level (no gaps)
- **Heart Rate:** 47–135 bpm with circadian patterns
- **Sleep Stages:** awake, light, deep, rem (realistic cycles)
- **Sleep Duration:** ~52 hours/week (realistic for healthy adult)
- **Confidence Scores:** 0.92–0.99 (device accuracy)
- **Total Data Points:** 13,183

**Realistic Patterns Included:**
- Circadian rhythm (lower HR during sleep, higher in afternoon)
- Activity spikes (15% occurrence during waking hours)
- Sleep architecture (~90-minute cycles)
- Gradual HR increase before waking
- Post-exercise recovery patterns

**Generator Options:**
```bash
# Custom patient ID
node generate_wearable_data.js --patient-id=pat-005

# Custom output file
node generate_wearable_data.js --output=custom_payload.json

# Both options
node generate_wearable_data.js --patient-id=pat-123 --output=/tmp/data.json
```

---

### Person 1 — Report Upload & Extraction Pipeline

**What you need:** Test PDFs + reference extraction data.

```bash
# Generate test PDF files
node generate_test_pdfs.js

# Output: test-pdfs/ directory with 3 reports
# - Thyroid_Function_Test_Mar2026.txt (NORMAL)
# - Kidney_Function_Test_Feb2026.txt (HIGH/CKD)
# - Diabetes_Monitoring_Panel_Jan2026.txt (CRITICAL)

# Test your extraction pipeline
for pdf in test-pdfs/*.txt; do
  curl -X POST http://localhost:5000/api/reports/extract \
    -F "file=@$pdf" \
    -F "patientId=pat-001"
done

# Validate against reference data
cat mock_report_extractions.json | jq '.reports[0].extractedData'
```

**Test Coverage:**

| Report | Type | Expected Result | Alert Count |
|--------|------|-----------------|------------|
| **Thyroid** | Normal panel | ✅ No alerts | 0 |
| **Kidney** | CKD detection | ⚠️ 1+ alert | 1 |
| **Diabetes** | Critical control | 🚨 3+ alerts | 3 |

**Reference Extraction Data (mock_report_extractions.json):**
- Complete extracted lab values
- Clinical interpretations
- Alert flags that should trigger
- AI summaries with confidence scores
- Recommendations by severity level

**Validation Workflow:**
```python
import json

# Load reference data
with open('mock_report_extractions.json') as f:
    reference = json.load(f)

# Extract your PDF
extracted = your_extraction_pipeline('test-pdfs/Thyroid_Function_Test_Mar2026.txt')

# Compare against reference
assert extracted['testResults'] == reference['reports'][0]['extractedData']['testResults']
print("✅ Extraction validated!")
```

---

## 📊 Data Quality Metrics

### UI Contracts (Doctor Roster)
- ✅ 5 patients with diverse health conditions
- ✅ 8 active alerts (high/medium/low severity mix)
- ✅ 10 sample reports across patients
- ✅ Realistic health metrics (not randomized)
- ✅ All required fields for UI mapping

### Wearable Data
- ✅ 7 full days = 10,080 data points per patient
- ✅ 13,183 total readings (heart rate + any metadata)
- ✅ Minute-level granularity with no gaps
- ✅ Circadian patterns validated
- ✅ Sleep stages follow realistic 90-min cycles
- ✅ Confidence scores: 0.92–0.99 range
- ✅ ~2.8 MB uncompressed for API testing

### Report Extraction Reference
- ✅ 3 diverse medical reports (normal/high/critical)
- ✅ Complete OCR text files provided
- ✅ Extracted structured JSON for all reports
- ✅ Lab values with reference ranges
- ✅ Alert flags for rule engine testing
- ✅ AI summaries with confidence scores (0.95–0.97)
- ✅ Recommendations mapped by severity

---

## 🎯 Integration Examples

### Frontend (React)

```jsx
import doctorRoster from '@/mock-data/mock_doctor_roster.json';
import PatientCard from '@/components/PatientCard';

export function DoctorDashboard() {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {doctorRoster.patientsUnderCare.map((patient) => (
        <PatientCard
          key={patient.patientId}
          name={patient.name}
          condition={patient.condition}
          alertCount={patient.activeAlertsCount}
          severity={patient.alertSeverity}
        />
      ))}
    </div>
  );
}
```

### Wearable API (Node/Express)

```javascript
const wearableData = require('./wearable_payload.json');

app.post('/api/wearable/ingest', async (req, res) => {
  const { dataPoints, metadata } = req.body;
  
  // Insert wearable data into time-series DB
  const result = await db.wearable.insertMany(dataPoints);
  
  // Validate circadian patterns
  const avgSleep = metadata.summary.avgSleepPerNight;
  if (avgSleep < 4 || avgSleep > 10) {
    return res.status(400).json({ error: 'Unrealistic sleep duration' });
  }
  
  res.status(201).json({ 
    success: true, 
    pointsIngested: result.insertedCount 
  });
});
```

### Report Pipeline (Python)

```python
import json
from pipeline import extract_report, generate_alerts

# Load reference data
with open('mock_report_extractions.json') as f:
    ref_data = json.load(f)

# Test each report
for report in ref_data['reports']:
    pdf_path = f"test-pdfs/{report['fileName']}"
    
    # Extract
    extracted = extract_report(pdf_path)
    
    # Validate structure
    assert 'testResults' in extracted
    assert 'alertFlags' in extracted
    
    # Validate alert counts
    expected_alerts = len(report['extractedData']['alertFlags'])
    actual_alerts = len(extracted['alertFlags'])
    assert actual_alerts == expected_alerts, f"Alert mismatch: {actual_alerts} != {expected_alerts}"
    
    print(f"✅ {report['fileName']} validated")
```

---

## 🔬 Technical Details

### Wearable Data Generator

The wearable data generator (`generate_wearable_data.js`) implements realistic physiology:

- **Circadian Rhythm:** ✅ Lower HR during sleep (47–65 bpm), higher during day (70–100 bpm)
- **Activity Response:** ✅ 15% activity chunks with 80% HR boost (up to 135 bpm)
- **Sleep Architecture:** ✅ 90-minute cycles with awake/light/deep/rem stages
- **Variability:** ✅ ±6 bpm random per-minute variation (realistic sensor noise)
- **Confidence:** ✅ 0.92–0.99 score per reading (modern Fitbit accuracy)

### Report Extraction Reference

The report extraction JSON (`mock_report_extractions.json`) provides:
- All lab values with reference ranges
- Clinical interpretation text
- Alert criteria mapped to flag codes
- AI-generated summaries with citations
- Recommendation severity-based triage

---

## 📋 Monday Handoff Checklist

- [ ] **Person 4:** Receives `mock_doctor_roster.json` and `mock_patient_detail.json`
- [ ] **Person 3:** Receives `generate_wearable_data.js` and runs it successfully
- [ ] **Person 1:** Receives test PDFs (run generator) and `mock_report_extractions.json`
- [ ] All teams confirm data is parseable and ready for integration
- [ ] All teams start building against mock data (no backend blocking)

---

## 🆘 Troubleshooting

### Wearable generator fails

```bash
# Ensure Node.js is available
node --version

# Permission issue?
chmod +x generate_wearable_data.js

# Run with explicit output
node generate_wearable_data.js --output=$(pwd)/payload.json
```

### Report PDFs not generating

```bash
# Check directory
mkdir -p test-pdfs

# Run generator with explicit output directory
node generate_test_pdfs.js --output-dir=$(pwd)/test-pdfs

# Verify files
ls -lh test-pdfs/
```

### JSON validation errors

```bash
# Validate JSON structure
jq . mock_doctor_roster.json
jq . mock_patient_detail.json
jq . wearable_payload.json
jq . mock_report_extractions.json

# Pretty print specific section
jq '.patientsUnderCare[0]' mock_doctor_roster.json
```

---

## 📞 Questions?

Refer to the main [README.md](../README.md) for platform architecture and data pipeline details.

---

**Status:** ✅ READY FOR MONDAY DELIVERY  
**Last Updated:** April 8, 2026  
**Version:** 1.0
