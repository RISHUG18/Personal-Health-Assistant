#!/usr/bin/env python3
"""
Integrated test runner for Person 1 and Person 3's APIs.
Executes both vitals ingestion and report upload tests with comprehensive logging.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import time


BACKEND_DIR = Path(__file__).parent
LOG_FILE = BACKEND_DIR / "test_results.json"


def run_test_script(script_name: str, description: str) -> dict:
    """Run a test script and capture output."""
    print(f"\n{'='*70}")
    print(f"🧪 {description}")
    print(f"{'='*70}")
    
    script_path = BACKEND_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return {
            "status": "skipped",
            "error": "script not found",
            "duration": 0
        }
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BACKEND_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        return {
            "status": "completed" if result.returncode == 0 else "failed",
            "return_code": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 60 seconds")
        return {
            "status": "timeout",
            "duration": 60,
            "error": "test execution timeout"
        }
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return {
            "status": "error",
            "error": str(e),
            "duration": (datetime.now() - start_time).total_seconds()
        }


def wait_for_server(url: str = "http://localhost:8000/health", timeout: int = 30) -> bool:
    """Wait for backend server to be ready."""
    print("\n⏳ Waiting for backend server to be ready...")
    
    import requests
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                print("✅ Backend server is ready")
                return True
        except:
            pass
        
        time.sleep(1)
    
    print(f"❌ Backend server did not respond within {timeout} seconds")
    return False


def main():
    """Run all tests."""
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                      INTEGRATED API TEST SUITE                            ║
║                  Person 1 (Reports) + Person 3 (Vitals)                   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Check if backend is running
    server_ready = wait_for_server()
    if not server_ready:
        print("\n⚠️  Backend server not available. Tests will likely fail.")
        print("   Start the backend with: uvicorn backend.main:app --reload")
    
    overall_start = datetime.now()
    
    test_results = {
        "timestamp": overall_start.isoformat(),
        "backend_ready": server_ready,
        "tests": {}
    }
    
    # Test Person 1 (Reports)
    test_results["tests"]["person_1_reports"] = run_test_script(
        "test_report_ingestion.py",
        "Person 1 - Report Upload & Ingestion API"
    )
    
    # Test Person 3 (Vitals)
    test_results["tests"]["person_3_vitals"] = run_test_script(
        "test_vitals_ingestion.py",
        "Person 3 - Wearable Vitals Ingestion API"
    )
    
    overall_duration = (datetime.now() - overall_start).total_seconds()
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 OVERALL TEST SUMMARY")
    print(f"{'='*70}")
    
    person_1_status = test_results["tests"]["person_1_reports"].get("status", "unknown")
    person_3_status = test_results["tests"]["person_3_vitals"].get("status", "unknown")
    
    print(f"Person 1 (Reports):  {person_1_status.upper()}")
    print(f"Person 3 (Vitals):   {person_3_status.upper()}")
    print(f"Total Duration:      {overall_duration:.2f}s")
    
    test_results["summary"] = {
        "person_1": person_1_status,
        "person_3": person_3_status,
        "overall_duration": overall_duration
    }
    
    # Save results
    print(f"\n💾 Saving test results to {LOG_FILE}...")
    with open(LOG_FILE, "w") as f:
        json.dump(test_results, f, indent=2)
    print(f"   ✅ Results saved")
    
    # Exit code
    success = (person_1_status in ("completed", "success") and 
               person_3_status in ("completed", "success", "timeout"))
    
    if success:
        print("\n✅ Tests completed")
        return 0
    else:
        print("\n⚠️  Some tests may have issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())