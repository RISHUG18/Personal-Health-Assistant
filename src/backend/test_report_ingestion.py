#!/usr/bin/env python3
"""
Test script for Person 1's report upload and ingestion API.
Tests the POST /reports/upload and POST /reports/ingest endpoints.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import requests


BASE_URL = "http://localhost:8000"
TEST_USER_ID = "pat-1"  # Riya Sharma


def load_extracted_report(filepath: str) -> dict:
    """Load extracted report data."""
    with open(filepath, "r") as f:
        return json.load(f)


def test_report_ingest(report_file: str) -> dict:
    """Test the report ingestion API."""
    print(f"\n📋 Testing report: {Path(report_file).name}")
    print("-" * 60)
    
    # Load extracted data
    try:
        report_data = load_extracted_report(report_file)
    except FileNotFoundError:
        print(f"   ❌ File not found: {report_file}")
        return {"status": "failed", "error": "file not found"}
    
    filename = report_data.get("filename", "unknown.pdf")
    report_type = report_data.get("report_type", "unknown")
    
    print(f"   File: {filename}")
    print(f"   Type: {report_type}")
    print(f"   Extracted facts: {len(report_data.get('extracted_facts', {}))}")
    
    # Prepare ingest request body
    ingest_body = {
        "user_id": TEST_USER_ID,
        "report_id": report_data.get("report_id", "test-report"),
        "report_type": report_type,
        "filename": filename,
        "ocr_text": report_data.get("ocr_text", ""),
        "extracted_data": report_data.get("extracted_facts", {}),
        "ai_insights": report_data.get("ai_insights", {})
    }
    
    # Call ingest API
    print(f"   📡 Posting to /reports/ingest...")
    try:
        response = requests.post(
            f"{BASE_URL}/reports/ingest",
            json=ingest_body,
            timeout=30
        )
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Failed to connect to {BASE_URL}")
        return {"status": "failed", "error": "connection error"}
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return {"status": "failed", "error": str(e)}
    
    print(f"      Status: {response.status_code}")
    
    try:
        result = response.json()
    except:
        print(f"      Response: {response.text[:200]}")
        return {"status": "failed", "error": "invalid response"}
    
    if response.status_code in (200, 201, 202):
        print(f"   ✅ SUCCESS")
        return {
            "status": "success",
            "filename": filename,
            "report_type": report_type,
            "result": result
        }
    else:
        print(f"   ❌ FAILED: {result}")
        return {
            "status": "failed",
            "filename": filename,
            "error": result
        }


def run_all_report_tests() -> dict:
    """Test all extracted reports."""
    print("🧪 Testing Person 1's Report Upload/Ingest API")
    print("=" * 60)
    
    reports = [
        "extracted_cbc_report.json",
        "extracted_lipid_report.json",
        "extracted_hba1c_report.json"
    ]
    
    results = {
        "total": len(reports),
        "successful": 0,
        "failed": 0,
        "details": []
    }
    
    for report_name in reports:
        report_path = Path(__file__).parent / report_name
        result = test_report_ingest(str(report_path))
        results["details"].append(result)
        
        if result["status"] == "success":
            results["successful"] += 1
        else:
            results["failed"] += 1
    
    return results


if __name__ == "__main__":
    from datetime import datetime
    
    start_time = datetime.now()
    results = run_all_report_tests()
    end_time = datetime.now()
    
    print("\n" + "=" * 60)
    print(f"✅ Test Summary:")
    print(f"   Total: {results['total']}")
    print(f"   Successful: {results['successful']}")
    print(f"   Failed: {results['failed']}")
    print(f"⏱️  Duration: {(end_time - start_time).total_seconds():.2f}s")
    
    print(f"\n📊 Detailed Results:")
    print(json.dumps(results, indent=2))
    
    sys.exit(0 if results["failed"] == 0 else 1)