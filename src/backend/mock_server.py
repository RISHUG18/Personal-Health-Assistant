"""
Mock Server for Health MVP API
==============================
A standalone mock backend for UI development and testing.
Run with: uvicorn mock_server:app --reload
Test at: http://127.0.0.1:8000/api/v1/dashboard/patient_001
"""

from fastapi import FastAPI, File, UploadFile, Form
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI(
    title="Health MVP Mock Server",
    description="Mock backend for UI development",
    version="1.0.0",
)

# --- MOCK DATA ---
MOCK_ALERTS = [
    {
        "id": "alert_01",
        "title": "Low Sleep Duration",
        "severity": "high",
        "timestamp": datetime.now().isoformat(),
        "message": "You slept less than 5 hours last night.",
        "evidence": {
            "source": "Apple Watch",
            "metric": "sleep_duration",
            "value": "4h 12m",
            "threshold": "6h 00m"
        }
    },
    {
        "id": "alert_02",
        "title": "Hydration Reminder",
        "severity": "low",
        "timestamp": datetime.now().isoformat(),
        "message": "Remember to drink water.",
        "evidence": None
    }
]


# --- ENDPOINTS ---

@app.get("/api/v1/dashboard/{user_id}")
def get_dashboard(user_id: str):
    """
    Simulates the main dashboard load.
    Returns static data for 'patient_001'.
    Use user_id='error_test' to simulate error state.
    """
    if user_id == "error_test":
        return {"status": "error", "message": "Simulated DB failure"}
        
    return {
        "status": "success",
        "data": {
            "user_id": user_id,
            "greeting": "Good Morning, Sarah",
            "wellbeing_score": 85,
            "wellbeing_trend": "improving",
            "active_alerts_count": len(MOCK_ALERTS),
            "environment": {
                "aqi": 42,
                "weather": "Sunny"
            }
        }
    }


@app.get("/api/v1/alerts")
def get_alerts(user_id: str):
    """
    Returns the mock alerts list.
    """
    return {
        "status": "success",
        "data": {
            "alerts": MOCK_ALERTS
        }
    }


class RagQuery(BaseModel):
    user_id: str
    query: str


@app.post("/api/v1/rag_query")
def post_rag_query(payload: RagQuery):
    """
    Simulates the AI answering a question about Iron levels.
    """
    return {
        "status": "success",
        "data": {
            "answer": "Your iron levels are low likely due to the recent drop in Ferritin observed in your blood test from Jan 12th.",
            "citations": [
                {
                    "source_file": "blood_report_jan12.pdf",
                    "page": 2,
                    "snippet": "Ferritin: 10 ng/mL (Reference: 30-400)"
                }
            ]
        }
    }


@app.post("/api/v1/reports/upload")
def upload_report(user_id: str = Form(...), file: UploadFile = File(...)):
    """
    Simulates a PDF upload.
    """
    return {
        "status": "processing",
        "report_id": "rep_12345",
        "message": f"Received {file.filename}. Extraction started."
    }


@app.get("/api/v1/doctor/patients")
def get_patients(doctor_id: str):
    """
    Simulates the doctor's patient list.
    """
    return {
        "patients": [
            {
                "user_id": "patient_001",
                "name": "Sarah Jones",
                "age": 34,
                "risk_level": "medium",
                "last_updated": datetime.now().isoformat()
            },
            {
                "user_id": "patient_002",
                "name": "Mike Ross",
                "age": 45,
                "risk_level": "high",
                "last_updated": "2023-10-26T14:30:00Z"
            }
        ]
    }


# Run with: uvicorn mock_server:app --reload
