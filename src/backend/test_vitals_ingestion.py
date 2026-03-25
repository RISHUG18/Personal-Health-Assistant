#!/usr/bin/env python3
"""
Test script for Person 3's wearable vitals ingestion API.
Generates realistic vitals data and tests the POST /api/v1/ingest/vitals endpoint.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE_URL = "http://localhost:8000"
TEST_USER_ID = "pat-1"  # Riya Sharma


def load_wearable_payload(filepath: str) -> dict:
    """Load the pre-generated wearable payload."""
    with open(filepath, "r") as f:
        return json.load(f)


def convert_to_vital_readings(payload: dict) -> list[dict]:
    """Convert wearable payload to VitalReading format for API."""
    readings = []
    
    # Convert heart rate readings
    for hr_data in payload.get("heart_rate", [])[:1000]:  # Limit to 1000 to avoid hitting API limits
        readings.append({
            "recorded_at": hr_data["timestamp"],
            "metric_type": "heart_rate",
            "value": hr_data["heart_rate"],
            "unit": "bpm",
            "device_id": "wearable_demo"
        })
    
    # Convert sleep data
    for sleep_data in payload.get("sleep", []):
        # Sleep duration (hours)
        readings.append({
            "recorded_at": f"{sleep_data['date']}T12:00:00Z",
            "metric_type": "sleep_hours",
            "value": sleep_data["total_duration_hours"],
            "unit": "hours",
            "device_id": "wearable_demo"
        })
        
        # Quality score
        readings.append({
            "recorded_at": f"{sleep_data['date']}T12:00:00Z",
            "metric_type": "sleep_quality",
            "value": sleep_data["quality_score"],
            "unit": "score",
            "device_id": "wearable_demo"
        })
    
    return readings


def test_vitals_ingestion(payload_file: str) -> dict:
    """Test the vitals ingestion API."""
    print("🧪 Testing Person 3's Vitals Ingestion API")
    print("=" * 60)
    
    # Load payload
    print(f"📂 Loading wearable payload from {payload_file}...")
    try:
        payload = load_wearable_payload(payload_file)
    except FileNotFoundError:
        print(f"❌ File not found: {payload_file}")
        return {"status": "failed", "error": "payload not found"}
    
    # Convert to API format
    print("🔄 Converting to VitalReading format...")
    readings = convert_to_vital_readings(payload)
    print(f"   Total readings: {len(readings)}")
    
    # Prepare request
    request_body = {
        "user_id": TEST_USER_ID,
        "readings": readings
    }
    
    # Call API
    print(f"\n📡 Posting to {BASE_URL}/api/v1/ingest/vitals...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ingest/vitals",
            json=request_body,
            timeout=30
        )
    except requests.exceptions.ConnectionError:
        print(f"❌ Failed to connect to {BASE_URL}")
        return {"status": "failed", "error": "connection error"}
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {"status": "failed", "error": str(e)}
    
    print(f"   Status: {response.status_code}")
    
    try:
        result = response.json()
    except:
        print(f"   Response: {response.text[:200]}")
        return {"status": "failed", "error": "invalid response"}
    
    if response.status_code in (200, 201, 202):
        print(f"\n✅ SUCCESS")
        print(f"   Inserted: {result.get('inserted', 0)}")
        print(f"   Skipped: {result.get('skipped', 0)}")
        print(f"   Total: {result.get('total', 0)}")
        if result.get('errors'):
            print(f"   Errors: {result['errors']}")
        return {"status": "success", "result": result}
    else:
        print(f"\n❌ FAILED")
        print(f"   Response: {result}")
        return {"status": "failed", "error": result}


if __name__ == "__main__":
    from datetime import datetime
    
    payload_file = Path(__file__).parent / "wearable_payload.json"
    
    start_time = datetime.now()
    result = test_vitals_ingestion(str(payload_file))
    end_time = datetime.now()
    
    print(f"\n⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
    print(f"\n📊 Result Summary:")
    print(json.dumps(result, indent=2))
    
    sys.exit(0 if result["status"] == "success" else 1)