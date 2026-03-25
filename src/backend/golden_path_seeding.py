#!/usr/bin/env python3
"""
Golden Path Seeding
Seeds production database with a compelling, end-to-end storyline:
Patient uploads blood test → Starts wearable sync → Cron job detects anomalies →
Alert generated → Doctor reviews → Patient asks via voice why they got the alert.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Mock database seed (demonstrating the data flow)
GOLDEN_PATH_SCENARIO = {
    "timeline": [
        {
            "timestamp": "2026-03-15T09:00:00Z",
            "event": "Patient Registration",
            "actor": "Patient (Riya Sharma)",
            "description": "Riya Sharma (pat-1) registers on the HealthAI app, authorizes doctor access, enables wearable sync"
        },
        {
            "timestamp": "2026-03-15T10:30:00Z",
            "event": "Report Upload",
            "actor": "Patient (Riya)",
            "description": "Uploads old CBC report (15-Jan-2026): Hemoglobin 9.8 g/dL (LOW - anaemia)"
        },
        {
            "timestamp": "2026-03-15T10:45:00Z",
            "event": "OCR Processing",
            "actor": "Backend (OCR Service)",
            "description": "OCR extracts: Hb 9.8, Serum Iron 42 µg/dL (both low); Facts stored in database"
        },
        {
            "timestamp": "2026-03-15T11:00:00Z",
            "event": "Wearable Data Sync Starts",
            "actor": "Patient (Wearable Device)",
            "description": "Apple Watch sends 7 days of historical data: Heart rates, sleep minutes. Ingested via POST /api/v1/ingest/vitals"
        },
        {
            "timestamp": "2026-03-15T11:15:00Z",
            "event": "Cron Job Triggers (Hourly)",
            "actor": "Backend (Alert Rules Engine)",
            "description": "Rules evaluate: Low Hb + AQI 145 (heatwave) + Sleep 5.8 hrs/day → Medium+ alert"
        },
        {
            "timestamp": "2026-03-15T11:20:00Z",
            "event": "Alert Generated",
            "actor": "Backend (Deterministic Rules)",
            "description": "Alert created: 'High AQI + Anaemia Risk' (severity=HIGH). Reason: Chennai heatwave + iron deficiency = infection risk. Evidence: CBC report + environment"
        },
        {
            "timestamp": "2026-03-15T11:25:00Z",
            "event": "Doctor Notified",
            "actor": "Backend (Notification Service)",
            "description": "Dr. Priya Nair receives push notification: 'Riya Sharma - HIGH alert: High AQI + Anaemia Risk'"
        },
        {
            "timestamp": "2026-03-15T14:30:00Z",
            "event": "Doctor Reviews Case",
            "actor": "Doctor (Dr. Priya Nair)",
            "description": "Dr. Priya logs into Doctor Dashboard. Sees Riya ranked #1 in patient priority list (3 active alerts). Clicks to drill in."
        },
        {
            "timestamp": "2026-03-15T14:35:00Z",
            "event": "Doctor Views Patient Summary",
            "actor": "Doctor (Dr. Priya)",
            "description": "Doctor Dashboard shows: Riya's health metrics, active alerts, report timeline, environment context (AQI 145, Temp 35°C)"
        },
        {
            "timestamp": "2026-03-15T14:40:00Z",
            "event": "Doctor Acknowledges Alert",
            "actor": "Doctor (Dr. Priya)",
            "description": "Doctor acknowledges the HIGH alert and adds clinical note: 'Recommend iron supplements + avoid excessive heat exposure'"
        },
        {
            "timestamp": "2026-03-15T18:00:00Z",
            "event": "Patient Uses Voice Assistant",
            "actor": "Patient (Riya) + Voice App",
            "description": "Riya asks: 'Why did I get an alert today?' Voice app converts to text, queries RAG pipeline"
        },
        {
            "timestamp": "2026-03-15T18:05:00Z",
            "event": "RAG Retrieval",
            "actor": "Backend (RAG Pipeline)",
            "description": "RAG retrieves context: CBC lab values (Hb 9.8), environment (AQI 145), sleep metrics, alert rule that fired"
        },
        {
            "timestamp": "2026-03-15T18:10:00Z",
            "event": "Gemini Response via Voice",
            "actor": "Backend (LLM) + Voice App",
            "description": "Gemini 2.5 Flash generates: 'You got an alert because your blood test shows low hemoglobin (9.8 g/dL), indicating anaemia. Combined with Chennai's high air quality index (145) and your recent sleep of 5.8 hours, this increases your infection risk. The doctor has recommended iron-rich foods and advised avoiding extreme heat. Here are 3 immediate steps...'"
        }
    ],
    "seed_data": {
        "patient": {
            "id": "pat-1",
            "email": "riya@example.com",
            "full_name": "Riya Sharma",
            "age": 28,
            "city": "Chennai",
            "role": "patient"
        },
        "doctor": {
            "id": "doc-1",
            "email": "priya@apollo.hospital",
            "full_name": "Dr. Priya Nair",
            "specialization": "General Practice",
            "hospital": "Apollo Hospitals Chennai",
            "role": "doctor"
        },
        "consent_record": {
            "patient_id": "pat-1",
            "doctor_id": "doc-1",
            "can_view_reports": True,
            "can_view_metrics": True,
            "can_add_comments": True,
            "created_at": "2026-03-15T09:30:00Z"
        },
        "report_upload": {
            "report_id": "rep-cbc-jan26",
            "patient_id": "pat-1",
            "filename": "CBC_Report_Jan2026.pdf",
            "upload_timestamp": "2026-03-15T10:30:00Z",
            "status": "processed",
            "extracted_facts": {
                "hemoglobin": 9.8,
                "hemoglobin_unit": "g/dL",
                "hemoglobin_flag": "LOW",
                "serum_iron": 42,
                "serum_iron_unit": "µg/dL",
                "serum_iron_flag": "LOW"
            }
        },
        "wearable_vitals_batch": {
            "patient_id": "pat-1",
            "sync_timestamp": "2026-03-15T11:00:00Z",
            "readings_count": 10080,
            "heart_rate_range": [55, 95],
            "sleep_average_hours": 5.8,
            "steps_average_day": 7500
        },
        "alert": {
            "alert_id": "alert-heatwave-anaemia",
            "patient_id": "pat-1",
            "severity": "HIGH",
            "title": "High AQI + Anaemia Risk",
            "reason": "Low hemoglobin (9.8 g/dL) combined with heatwave and poor sleep increases infection risk",
            "generated_at": "2026-03-15T11:20:00Z",
            "acknowledged_by_doctor": True,
            "acknowledged_at": "2026-03-15T14:40:00Z",
            "doctor_notes": "Recommend iron supplements + avoid excessive heat exposure"
        },
        "voice_interaction": {
            "patient_id": "pat-1",
            "query": "Why did I get an alert today?",
            "timestamp": "2026-03-15T18:00:00Z",
            "context_retrieved": {
                "relevant_reports": ["rep-cbc-jan26"],
                "relevant_environment": {"aqi": 145, "temperature": 35},
                "relevant_metrics": {"sleep_hours": 5.8, "average_hr": 78},
                "triggered_alert": "alert-heatwave-anaemia"
            },
            "response": "You got an alert because your blood test shows low hemoglobin (9.8 g/dL), indicating anaemia. Combined with Chennai's high air quality index (145) and your recent sleep of 5.8 hours, this increases your infection risk. The doctor has recommended iron-rich foods and advised avoiding extreme heat.",
            "response_tokens": 87,
            "model": "gemini-2.5-flash",
            "latency_ms": 234
        }
    }
}


def generate_sql_seed_statements() -> str:
    """Generate SQL seed statements for the golden path."""
    sql = []
    
    # Patients
    sql.append(f"""
    INSERT INTO public.users (id, email, full_name, role, created_at)
    VALUES ('pat-1', 'riya@example.com', 'Riya Sharma', 'patient', '2026-03-15T09:00:00Z');
    """)
    
    # Doctors
    sql.append(f"""
    INSERT INTO public.users (id, email, full_name, role, created_at)
    VALUES ('doc-1', 'priya@apollo.hospital', 'Dr. Priya Nair', 'doctor', '2026-03-15T08:00:00Z');
    """)
    
    # Consent Record
    sql.append(f"""
    INSERT INTO public.doctor_consent (patient_id, doctor_id, can_view_reports, can_view_metrics, can_add_comments, created_at)
    VALUES ('pat-1', 'doc-1', true, true, true, '2026-03-15T09:30:00Z');
    """)
    
    # Report Upload
    sql.append(f"""
    INSERT INTO public.reports (id, patient_id, filename, file_path, report_type, upload_date, processing_status, created_at)
    VALUES ('rep-cbc-jan26', 'pat-1', 'CBC_Report_Jan2026.pdf', '/uploads/CBC_Report_Jan2026.pdf', 'blood_test', '2026-03-15', 'completed', '2026-03-15T10:30:00Z');
    """)
    
    # Extracted Lab Values
    sql.append(f"""
    INSERT INTO public.lab_values (report_id, metric_name, value, unit, reference_range, flag, created_at)
    VALUES
      ('rep-cbc-jan26', 'hemoglobin', 9.8, 'g/dL', '12-16', 'LOW', '2026-03-15T10:45:00Z'),
      ('rep-cbc-jan26', 'serum_iron', 42, 'µg/dL', '50-170', 'LOW', '2026-03-15T10:45:00Z');
    """)
    
    # Vitals Metrics
    sql.append(f"""
    INSERT INTO public.wearable_vitals (patient_id, recorded_at, metric_type, value, unit, device_id, created_at)
    VALUES
      ('pat-1', '2026-03-15T10:00:00Z', 'heart_rate', 72, 'bpm', 'apple_watch', '2026-03-15T11:00:00Z'),
      ('pat-1', '2026-03-15T20:00:00Z', 'sleep_minutes', 348, 'min', 'apple_watch', '2026-03-15T11:00:00Z');
    """)
    
    # Alert Generated
    sql.append(f"""
    INSERT INTO public.alerts (id, patient_id, severity, title, description, triggered_by_rule, acknowledged_at, created_at)
    VALUES ('alert-heatwave-anaemia', 'pat-1', 'high', 'High AQI + Anaemia Risk', 
            'Low hemoglobin combined with heatwave and poor sleep increases infection risk', 
            'rule_high_aqi_and_anaemia', '2026-03-15T14:40:00Z', '2026-03-15T11:20:00Z');
    """)
    
    # Environment Data
    sql.append(f"""
    INSERT INTO public.environment (patient_id, city, aqi, temperature, humidity, recorded_at, created_at)
    VALUES ('pat-1', 'Chennai', 145, 35, 67, '2026-03-15T11:00:00Z', '2026-03-15T11:00:00Z');
    """)
    
    return "\n".join(sql)


if __name__ == "__main__":
    print("=" * 80)
    print("🎯 GOLDEN PATH SCENARIO - END-TO-END STORYLINE")
    print("=" * 80)
    
    print("\n📖 Timeline:")
    for event in GOLDEN_PATH_SCENARIO["timeline"]:
        print(f"\n  {event['timestamp']}")
        print(f"  🔹 {event['event']} ({event['actor']})")
        print(f"     {event['description']}")
    
    print("\n\n💾 Seed Data Summary:")
    print(json.dumps(GOLDEN_PATH_SCENARIO["seed_data"], indent=2))
    
    print("\n\n📝 SQL Seed Statements:")
    print(generate_sql_seed_statements())
    
    print("\n\n✅ Golden Path Scenario Documentation Complete")