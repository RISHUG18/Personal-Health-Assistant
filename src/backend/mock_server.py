"""
Mock Server for Vitalis Health MVP API
=======================================
A standalone FastAPI mock backend for UI development and testing.
No database, no Supabase, no API keys required.

Run with:
    cd src/backend
    uvicorn mock_server:app --reload --host 0.0.0.0 --port 8000

Test at:
    http://127.0.0.1:8000/docs   ← Swagger UI (all endpoints)

Special test IDs:
    user_id="error_test"    → returns simulated server error
    user_id="empty_test"    → returns empty data (no alerts, no patients)
    report_id="bad_report"  → returns 400 extraction error
"""

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Vitalis Health MVP — Mock Server",
    description="Offline mock backend for UI development. No external dependencies.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the HTML frontend (file://) and any local dev server to call this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static mock data ──────────────────────────────────────────────────────────

_NOW = datetime.now().isoformat()

_MOCK_ALERTS = [
    {
        "id": "alert_01",
        "title": "Low Sleep Duration",
        "severity": "high",
        "timestamp": _NOW,
        "message": "You slept less than 5 hours last night.",
        "evidence": {
            "source": "Apple Watch",
            "metric": "sleep_duration",
            "value": "4h 12m",
            "threshold": "6h 00m",
            "source_filename": "sleep_report_march.pdf",
            "source_url": "https://example.com/reports/sleep_report_march.pdf",
            "page_number": 1,
        },
    },
    {
        "id": "alert_02",
        "title": "Elevated Resting Heart Rate",
        "severity": "medium",
        "timestamp": _NOW,
        "message": "Your resting heart rate averaged 95 bpm over the last 3 days.",
        "evidence": {
            "source": "Fitbit",
            "metric": "resting_hr",
            "value": "95 bpm",
            "threshold": "80 bpm",
        },
    },
    {
        "id": "alert_03",
        "title": "Hydration Reminder",
        "severity": "low",
        "timestamp": _NOW,
        "message": "You have not logged water intake today.",
        "evidence": None,
    },
]

_MOCK_CITATIONS = [
    {
        "source_file": "blood_test_jan.pdf",
        "page": 2,
        "snippet": "Haemoglobin: 10.2 g/dL (reference: 12.0–16.0 g/dL). Below normal range.",
        "source_filename": "blood_test_jan.pdf",
        "source_url": "https://example.com/reports/blood_test_jan.pdf",
        "page_number": 2,
    },
    {
        "source_file": "lipid_panel_feb.pdf",
        "page": 1,
        "snippet": "Total Cholesterol: 215 mg/dL. LDL: 140 mg/dL. HDL: 48 mg/dL.",
        "source_filename": "lipid_panel_feb.pdf",
        "source_url": "https://example.com/reports/lipid_panel_feb.pdf",
        "page_number": 1,
    },
]

_MOCK_PATIENTS = [
    {
        "user_id": "patient_001",
        "name": "Ananya Sharma",
        "age": 34,
        "risk_level": "high",
        "last_updated": _NOW,
    },
    {
        "user_id": "patient_002",
        "name": "Ravi Menon",
        "age": 52,
        "risk_level": "medium",
        "last_updated": _NOW,
    },
    {
        "user_id": "patient_003",
        "name": "Priya Nair",
        "age": 28,
        "risk_level": "low",
        "last_updated": _NOW,
    },
]

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def healthcheck():
    return {"status": "ok", "server": "mock"}


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/dashboard/{user_id}", tags=["dashboard"])
def get_dashboard(user_id: str):
    """
    Returns the main dashboard summary for a user.

    - ``error_test`` → 500 simulated error
    - ``empty_test``  → success with zero alerts
    - anything else  → standard mock data
    """
    if user_id == "error_test":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulated DB failure",
        )

    active_alerts = 0 if user_id == "empty_test" else len(_MOCK_ALERTS)

    return {
        "status": "success",
        "data": {
            "user_id": user_id,
            "greeting": f"Good morning!",
            "wellbeing_score": 72,
            "wellbeing_trend": "stable",
            "active_alerts_count": active_alerts,
            "environment": {
                "aqi": 85,
                "weather": "Partly Cloudy",
            },
        },
    }


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.get("/api/v1/alerts", tags=["alerts"])
def get_alerts(user_id: str):
    """
    Returns health alerts for a user.

    - ``error_test`` → 500 simulated error
    - ``empty_test``  → empty alert list
    - anything else  → three sample alerts
    """
    if user_id == "error_test":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulated alert fetch failure",
        )

    alerts = [] if user_id == "empty_test" else _MOCK_ALERTS

    return {
        "status": "success",
        "data": {"alerts": alerts},
    }


# ── RAG / AI Health Assistant ──────────────────────────────────────────────────

class _RagQueryBody:
    pass


@app.post("/api/v1/rag_query", tags=["rag"])
async def rag_query(body: dict):
    """
    Simulates the RAG pipeline response.
    Accepts any JSON body (mirrors RagQueryRequest schema).
    """
    user_id = body.get("user_id", "unknown")
    query = body.get("query", "")

    if user_id == "error_test":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Simulated LLM failure",
        )

    return {
        "status": "success",
        "data": {
            "answer": (
                f"Based on your recent lab results, your haemoglobin levels are slightly "
                f"below the normal range. I recommend discussing iron supplementation with "
                f"your doctor. Your cholesterol profile also warrants attention — LDL is "
                f"mildly elevated. Query received: \"{query}\"."
            ),
            "citations": _MOCK_CITATIONS,
        },
    }


# ── Report Upload ─────────────────────────────────────────────────────────────

@app.post("/reports/upload", status_code=status.HTTP_201_CREATED, tags=["reports"])
async def upload_report(
    user_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Simulates uploading a medical report to storage."""
    filename = file.filename or "report.pdf"
    fake_path = f"reports/{user_id}/{_NOW[:10]}/{filename}"
    return {
        "status": "success",
        "report_id": "mock-report-abc123",
        "message": f"Report '{filename}' uploaded successfully.",
        "path": fake_path,
        "public_url": f"https://example.com/storage/{fake_path}",
    }


# ── Report OCR ────────────────────────────────────────────────────────────────

@app.post("/reports/ocr", tags=["reports"])
async def ocr_report(
    user_id: str = Form(...),
    storage_path: str = Form(...),
):
    """Simulates running OCR on an uploaded report."""
    if user_id == "error_test":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulated OCR failure: could not read file",
        )

    return {
        "path": storage_path,
        "ocr_text": (
            "PATIENT: John Doe  DOB: 01/01/1980\n"
            "TEST DATE: 2026-02-15\n\n"
            "COMPLETE BLOOD COUNT\n"
            "Haemoglobin: 10.2 g/dL  [Ref: 12.0-16.0]\n"
            "WBC: 7.4 x10^3/uL  [Ref: 4.5-11.0]\n"
            "Platelets: 210 x10^3/uL  [Ref: 150-400]\n\n"
            "LIPID PANEL\n"
            "Total Cholesterol: 215 mg/dL\n"
            "LDL: 140 mg/dL  HDL: 48 mg/dL\n"
        ),
        "confidence": 0.93,
        "report_id": "mock-report-abc123",
    }


# ── Extract Labs (Regex) ───────────────────────────────────────────────────────

@app.post("/reports/extract-labs", tags=["reports"])
async def extract_labs(report_id: str = Form(...)):
    """Simulates deterministic regex lab extraction."""
    if report_id == "bad_report":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OCR text found for this report",
        )

    return {
        "report_id": report_id,
        "inserted": 5,
    }


# ── Extract Labs (Gemini) ─────────────────────────────────────────────────────

@app.post("/reports/extract-labs-gemini", tags=["reports"])
async def extract_labs_gemini(report_id: str = Form(...)):
    """Simulates Gemini AI lab extraction (idempotent)."""
    if report_id == "bad_report":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OCR text found for this report",
        )

    return {
        "report_id": report_id,
        "total_tests_found": 6,
        "tests_inserted": 5,
        "tests_skipped": 1,
        "skipped_details": ["Duplicate entry: Haemoglobin already present"],
        "errors": [],
        "warnings": ["OCR confidence below 0.95 — results may be approximate"],
    }


# ── Full Pipeline ─────────────────────────────────────────────────────────────

@app.post("/reports/process", status_code=status.HTTP_201_CREATED, tags=["reports"])
async def process_report(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    use_gemini: bool = Form(False),
):
    """Simulates the full upload → OCR → extraction pipeline."""
    if user_id == "error_test":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulated pipeline failure at upload step",
        )

    filename = file.filename or "report.pdf"
    fake_path = f"reports/{user_id}/{_NOW[:10]}/{filename}"
    report_id = "mock-report-abc123"

    gemini_result = None
    if use_gemini:
        gemini_result = {
            "report_id": report_id,
            "total_tests_found": 6,
            "tests_inserted": 5,
            "tests_skipped": 1,
            "skipped_details": ["Duplicate: Haemoglobin"],
            "errors": [],
            "warnings": [],
        }

    return {
        "report_id": report_id,
        "storage_path": fake_path,
        "public_url": f"https://example.com/storage/{fake_path}",
        "ocr_confidence": 0.93,
        "ocr_text_preview": (
            "PATIENT: John Doe  DOB: 01/01/1980\n"
            "Haemoglobin: 10.2 g/dL  Total Cholesterol: 215 mg/dL ..."
        ),
        "regex_extraction": {
            "inserted": 5,
            "error": None,
        },
        "gemini_extraction": gemini_result,
        "gemini_error": None,
    }


# ── Doctor — Patient List ─────────────────────────────────────────────────────

@app.get("/api/v1/doctor/patients", tags=["doctor"])
def get_patients(doctor_id: str):
    """Returns the patient list for a doctor."""
    if doctor_id == "error_test":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Simulated patient list fetch failure",
        )

    patients = [] if doctor_id == "empty_test" else _MOCK_PATIENTS

    return {"patients": patients}
