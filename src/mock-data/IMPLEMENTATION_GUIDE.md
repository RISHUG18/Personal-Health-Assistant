# Implementation Examples

> Copy-paste ready code snippets showing how each team integrates the mock data.

---

## Person 4 — Frontend (React Components)

### Setup in Next.js

```typescript
// app/lib/mockData.ts
import doctorRoster from '@/mock-data/mock_doctor_roster.json';
import patientDetail from '@/mock-data/mock_patient_detail.json';

export const mockDoctorData = doctorRoster;
export const mockPatientData = patientDetail;
```

### Doctor Dashboard Example

```tsx
// app/doctor/page.tsx
'use client';

import { mockDoctorData } from '@/lib/mockData';
import AlertBadge from '@/components/ui/AlertBadge';

export default function DoctorDashboard() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Patient Roster</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {mockDoctorData.patientsUnderCare.map((patient) => (
          <div
            key={patient.patientId}
            className="border border-slate-700 rounded-lg p-4 hover:bg-slate-900/50"
          >
            {/* Patient Header */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="font-semibold text-lg">{patient.name}</h2>
                <p className="text-sm text-slate-400">{patient.condition}</p>
              </div>
              <AlertBadge 
                count={patient.activeAlertsCount}
                severity={patient.alertSeverity}
              />
            </div>

            {/* Health Metrics */}
            <div className="grid grid-cols-2 gap-2 text-sm mb-4">
              <div>
                <span className="text-slate-400">Steps/day</span>
                <p className="font-semibold">
                  {patient.healthMetrics.avgStepsPerDay.toLocaleString()}
                </p>
              </div>
              <div>
                <span className="text-slate-400">Sleep</span>
                <p className="font-semibold">
                  {patient.healthMetrics.avgSleepHours}h
                </p>
              </div>
              <div>
                <span className="text-slate-400">Heart Rate</span>
                <p className="font-semibold">
                  {patient.healthMetrics.avgHeartRate} bpm
                </p>
              </div>
              <div>
                <span className="text-slate-400">BP</span>
                <p className="font-semibold">
                  {patient.healthMetrics.bloodPressure}
                </p>
              </div>
            </div>

            {/* Recent Reports */}
            <div className="text-sm text-slate-400">
              <p>Recent Reports: {patient.recentReports.length}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Patient Detail View

```tsx
// app/patient/[id]/page.tsx
'use client';

import { mockPatientData } from '@/lib/mockData';
import AlertCard from '@/components/ui/AlertCard';
import ReportList from '@/components/ReportList';

export default function PatientDetail({ params }: { params: { id: string } }) {
  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{mockPatientData.name}</h1>
        <p className="text-slate-400">
          {mockPatientData.age} years old • {mockPatientData.gender}
        </p>
      </div>

      {/* Active Alerts */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Active Alerts</h2>
        <div className="space-y-3">
          {mockPatientData.activeAlerts.map((alert) => (
            <AlertCard
              key={alert.alertId}
              alert={alert}
              onAcknowledge={() => handleAcknowledge(alert.alertId)}
            />
          ))}
        </div>
      </section>

      {/* Recent Reports */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Medical Reports</h2>
        <ReportList reports={mockPatientData.recentReports} />
      </section>

      {/* 7-Day Health Trends */}
      <section>
        <h2 className="text-xl font-semibold mb-4">7-Day Trends</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <TrendChart
            title="Steps"
            data={mockPatientData.healthMetrics.sevenDayTrend.map(d => d.steps)}
          />
          <TrendChart
            title="Sleep (hours)"
            data={mockPatientData.healthMetrics.sevenDayTrend.map(d => d.sleepHours)}
          />
          <TrendChart
            title="Heart Rate"
            data={mockPatientData.healthMetrics.sevenDayTrend.map(d => d.avgHeartRate)}
          />
        </div>
      </section>
    </div>
  );
}
```

---

## Person 3 — Wearable API (Node/Express/FastAPI)

### Node.js Express Example

```javascript
// routes/wearable.js
const express = require('express');
const router = express.Router();
const wearablePayload = require('../mock-data/wearable_payload.json');

// Test endpoint: POST /api/wearable/ingest
router.post('/ingest', async (req, res) => {
  try {
    const { dataPoints, metadata } = req.body;

    if (!dataPoints || !Array.isArray(dataPoints)) {
      return res.status(400).json({
        error: 'Invalid payload: dataPoints array required'
      });
    }

    // Validate circadian patterns
    const nightHR = dataPoints
      .filter(d => {
        const hour = new Date(d.timestamp).getHours();
        return hour >= 22 || hour <= 6;
      })
      .map(d => d.heartRate);

    const avgNightHR = nightHR.reduce((a, b) => a + b) / nightHR.length;

    if (avgNightHR > 85) {
      return res.status(400).json({
        error: 'Unrealistic night HR — should be lower during sleep',
        avgNightHR
      });
    }

    // Insert into database
    const result = await db.wearable.insertMany(dataPoints);

    res.status(201).json({
      success: true,
      pointsIngested: result.insertedCount,
      metadata: metadata,
      summary: {
        avgHeartRate: Math.round(
          dataPoints.reduce((a, b) => a + b.heartRate, 0) / dataPoints.length
        ),
        heartRateRange: [
          Math.min(...dataPoints.map(d => d.heartRate)),
          Math.max(...dataPoints.map(d => d.heartRate))
        ]
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Test endpoint: LOAD mock data
router.get('/test/load-mock', async (req, res) => {
  try {
    const result = await db.wearable.insertMany(
      wearablePayload.dataPoints
    );
    res.json({
      success: true,
      pointsLoaded: result.insertedCount,
      patient: wearablePayload.metadata.patientId
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
```

### Python FastAPI Example

```python
# routes/wearable.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime

router = APIRouter(prefix="/api/wearable", tags=["wearable"])

class WearableDataPoint(BaseModel):
    timestamp: str
    date: str
    hour: int
    heartRate: int
    heartRateConfidence: float
    sleep: Optional[dict] = None
    deviceBattery: float

class WearablePayload(BaseModel):
    metadata: dict
    summary: dict
    dataPoints: List[WearableDataPoint]

@router.post("/ingest")
async def ingest_wearable(payload: WearablePayload):
    """Ingest wearable data and validate circadian patterns"""
    
    try:
        data_points = payload.dataPoints
        
        # Validate minimum data
        if len(data_points) < 1000:
            raise HTTPException(
                status_code=400,
                detail="Expected at least 7 days of data (10,080 points)"
            )
        
        # Check circadian patterns
        night_hours = [d for d in data_points 
                      if int(d.hour) >= 22 or int(d.hour) <= 6]
        day_hours = [d for d in data_points 
                    if 8 <= int(d.hour) <= 20]
        
        avg_night_hr = sum(d.heartRate for d in night_hours) / len(night_hours)
        avg_day_hr = sum(d.heartRate for d in day_hours) / len(day_hours)
        
        if avg_night_hr > 85:
            raise HTTPException(
                status_code=400,
                detail=f"Unrealistic night HR: {avg_night_hr:.0f} (should be 50-70)"
            )
        
        if avg_day_hr < 60:
            raise HTTPException(
                status_code=400,
                detail=f"Unrealistic day HR: {avg_day_hr:.0f} (should be 60-90)"
            )
        
        # Insert into database
        db_result = await db.wearable.insert_many([
            dp.model_dump() for dp in data_points
        ])
        
        return {
            "success": True,
            "pointsIngested": len(db_result.inserted_ids),
            "patientId": payload.metadata['patientId'],
            "circadianValidation": {
                "avgNightHR": round(avg_night_hr, 1),
                "avgDayHR": round(avg_day_hr, 1),
                "status": "valid"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/load-mock")
async def load_mock_data():
    """Load mock wearable payload for testing"""
    
    with open('../mock-data/wearable_payload.json') as f:
        payload = json.load(f)
    
    result = await db.wearable.insert_many(payload['dataPoints'])
    
    return {
        "success": True,
        "pointsLoaded": len(result.inserted_ids),
        "patientId": payload['metadata']['patientId'],
        "summary": payload['summary']
    }
```

### Manual Test

```bash
# Load mock wearable data
curl -X POST http://localhost:5000/api/wearable/ingest \
  -H "Content-Type: application/json" \
  -d @wearable_payload.json

# Expected response:
# HTTP 201 Created
# {
#   "success": true,
#   "pointsIngested": 10080,
#   "patientId": "pat-001",
#   "summary": {
#     "avgHeartRate": 67,
#     "avgSleepPerNight": 8
#   }
# }
```

---

## Person 1 — Report Upload & Extraction (Python)

### OCR Pipeline Test

```python
# tests/test_report_extraction.py
import json
from pathlib import Path
from extraction_pipeline import extract_report, generate_alerts

def test_report_extraction():
    """Test extraction pipeline against reference data"""
    
    # Load reference data
    with open('../mock-data/mock_report_extractions.json') as f:
        reference_data = json.load(f)
    
    test_dir = Path('../mock-data/test-pdfs')
    
    # Test each report
    for ref_report in reference_data['reports']:
        pdf_path = test_dir / ref_report['fileName']
        
        print(f"\n📄 Testing {ref_report['fileName']}")
        print(f"   Expected alerts: {len(ref_report['extractedData']['alertFlags'])}")
        
        # Extract from PDF
        extracted = extract_report(str(pdf_path))
        
        # Validate structure
        assert 'testResults' in extracted, "Missing testResults"
        assert 'alertFlags' in extracted, "Missing alertFlags"
        
        # Validate test count
        assert len(extracted['testResults']) == len(ref_report['extractedData']['testResults']), \
            f"Test count mismatch: {len(extracted)} != {len(ref_report['extractedData']['testResults'])}"
        
        # Validate each test result
        for i, (extracted_test, ref_test) in enumerate(
            zip(extracted['testResults'], ref_report['extractedData']['testResults'])
        ):
            assert extracted_test['testName'] == ref_test['testName'], \
                f"Test {i} name mismatch"
            
            assert abs(extracted_test['value'] - ref_test['value']) < 0.1, \
                f"Test {i} value mismatch: {extracted_test['value']} != {ref_test['value']}"
            
            assert extracted_test['status'] == ref_test['status'], \
                f"Test {i} status mismatch: {extracted_test['status']} != {ref_test['status']}"
        
        # Validate alert flags
        expected_alerts = set(ref_report['extractedData']['alertFlags'])
        actual_alerts = set(extracted['alertFlags'])
        
        assert actual_alerts == expected_alerts, \
            f"Alert mismatch: {actual_alerts} != {expected_alerts}"
        
        print(f"   ✅ PASSED — {len(extracted['testResults'])} tests, {len(extracted['alertFlags'])} alerts")
    
    print("\n✅ All tests passed!")

def test_alert_generation():
    """Test alert rule engine against reference data"""
    
    with open('../mock-data/mock_report_extractions.json') as f:
        reference_data = json.load(f)
    
    test_cases = [
        ("Thyroid", 0, "none"),      # Normal → 0 alerts
        ("Kidney", 1, "medium"),     # CKD → 1 alert
        ("Diabetes", 3, "critical"), # Poor control → 3+ alerts
    ]
    
    for report_name, expected_alert_count, expected_severity in test_cases:
        ref_report = next(r for r in reference_data['reports'] 
                         if report_name in r['fileName'])
        
        # Generate alerts from extracted data
        alerts = generate_alerts(ref_report['extractedData'])
        
        assert len(alerts) == expected_alert_count, \
            f"{report_name}: Expected {expected_alert_count} alerts, got {len(alerts)}"
        
        if expected_alert_count > 0:
            max_severity = max(a['severity'] for a in alerts)
            assert max_severity == expected_severity, \
                f"{report_name}: Expected {expected_severity}, got {max_severity}"
        
        print(f"✅ {report_name}: {len(alerts)} alerts, severity {expected_severity}")

if __name__ == "__main__":
    test_report_extraction()
    print()
    test_alert_generation()
```

### Upload API Test

```python
# tests/test_upload_api.py
import requests
import json

BASE_URL = "http://localhost:5000"

def test_thyroid_upload():
    """Test normal report - should have 0 alerts"""
    with open('../mock-data/test-pdfs/Thyroid_Function_Test_Mar2026.txt', 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f'{BASE_URL}/api/reports/extract',
            files=files,
            data={'patientId': 'pat-001'}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data['alerts']) == 0, "Thyroid should have no alerts"
    print("✅ Thyroid test passed")

def test_kidney_upload():
    """Test high CKD - should have kidney impairment alert"""
    with open('../mock-data/test-pdfs/Kidney_Function_Test_Feb2026.txt', 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f'{BASE_URL}/api/reports/extract',
            files=files,
            data={'patientId': 'pat-002'}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data['alerts']) >= 1, "Kidney should have at least 1 alert"
    assert any('kidney' in a['flag'].lower() for a in data['alerts']), \
        "Should have kidney-related alert"
    print("✅ Kidney test passed")

def test_diabetes_upload():
    """Test critical diabetes - should have 3+ alerts"""
    with open('../mock-data/test-pdfs/Diabetes_Monitoring_Panel_Jan2026.txt', 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f'{BASE_URL}/api/reports/extract',
            files=files,
            data={'patientId': 'pat-003'}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data['alerts']) >= 3, "Diabetes should have 3+ alerts"
    
    severity_counts = {}
    for alert in data['alerts']:
        severity = alert.get('severity', 'unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    assert 'critical' in severity_counts, "Should have critical alerts"
    print(f"✅ Diabetes test passed — {severity_counts}")

if __name__ == "__main__":
    test_thyroid_upload()
    test_kidney_upload()
    test_diabetes_upload()
    print("\n✅ All upload tests passed!")
```

---

## Integration Checklist

### Person 4 (UI)
- [ ] Copy mock_doctor_roster.json to src/data/
- [ ] Copy mock_patient_detail.json to src/data/
- [ ] Review JSON structure for schema match
- [ ] Render PatientCard component with roster data
- [ ] Render PatientDetail page with full patient view
- [ ] Test alert badge display with 3 severity levels
- [ ] Test 7-day trend sparklines

### Person 3 (Wearable API)
- [ ] Run `node generate_wearable_data.js`
- [ ] POST wearable_payload.json to /api/wearable/ingest
- [ ] Verify 10,080 records inserted
- [ ] Query back and check circadian patterns
- [ ] Validate sleep stage distribution
- [ ] Test confidence score filtering

### Person 1 (Reports)  
- [ ] Run `node generate_test_pdfs.js`
- [ ] Upload all 3 test PDFs to extraction API
- [ ] Validate extracted data matches reference
- [ ] Test alert generation for each severity level
- [ ] Verify confidence scores (0.95+)
- [ ] Test rule engine against all alert flags

---

**Last Updated:** April 8, 2026  
**Version:** 1.0
