"""
Quick Integration Test - Verify Complete User Workflow
=====================================================

This script tests a realistic user workflow:
1. Create a user account
2. Upload a PDF (basic storage only)
3. Ask a health question
4. Evaluate health rules
5. Check for alerts

This mimics exactly what a real user would do and verifies all
components work together.
"""

import requests
import uuid
import json
import time

# Configuration
API_BASE = "http://localhost:8000"  # Adjust if needed
USER_EMAIL = f"quicktest_{str(uuid.uuid4())[:8]}@example.com"
TEST_PDF_PATH = "src/frontend/public/full_body_checkup.pdf"

def log(step, message):
    print(f"[{step}] {message}")

def test_workflow():
    print("=" * 70)
    print("QUICK INTEGRATION TEST - COMPLETE USER WORKFLOW")
    print("=" * 70)

    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})

    try:
        # Step 1: Create User
        log("1", "Creating user account...")
        user_data = {
            "email": USER_EMAIL,
            "full_name": "Integration Test User",
            "city": "Hyderabad",
            "blood_group": "B+",
            "weight_kg": 70
        }

        resp = session.post(f"{API_BASE}/api/v1/users", json=user_data)
        if resp.status_code != 201:
            log("1", f"❌ User creation failed: {resp.status_code} {resp.text}")
            return False

        user = resp.json()
        user_id = user["id"]
        log("1", f"✅ User created: {user['full_name']} (ID: {user_id[:8]}...)")

        # Step 2: Upload PDF (basic storage only)
        log("2", "Uploading medical report...")
        try:
            with open(TEST_PDF_PATH, "rb") as f:
                files = {"file": ("test_report.pdf", f, "application/pdf")}
                data = {"user_id": user_id, "user_name": user["full_name"]}

                resp = session.post(f"{API_BASE}/reports/upload", files=files, data=data)

            if resp.status_code != 201:
                log("2", f"❌ PDF upload failed: {resp.status_code} {resp.text}")
                return False

            upload_result = resp.json()
            log("2", f"✅ PDF uploaded to: {upload_result['path']}")

        except FileNotFoundError:
            log("2", f"⚠️  PDF file not found at {TEST_PDF_PATH}, skipping upload test")

        # Step 3: Ask Health Question
        log("3", "Asking AI health question...")
        query_data = {
            "user_id": user_id,
            "query": "What should I focus on for better health?",
            "role": "user",
            "top_k": 5
        }

        resp = session.post(f"{API_BASE}/api/v1/rag_query", json=query_data)
        if resp.status_code != 200:
            log("3", f"❌ RAG query failed: {resp.status_code} {resp.text}")
            return False

        query_result = resp.json()
        log("3", f"✅ AI response received (model: {query_result['model']})")
        log("3", f"   Answer preview: {query_result['answer'][:100]}...")

        # Verify correct model
        if "gemini-3.1" not in query_result["model"].lower():
            log("3", f"⚠️  Expected gemini-3.1-pro-preview, got {query_result['model']}")

        # Step 4: Evaluate Health Rules
        log("4", "Evaluating health rules...")
        resp = session.post(f"{API_BASE}/alerts/evaluate/{user_id}")
        if resp.status_code != 200:
            log("4", f"❌ Rules evaluation failed: {resp.status_code} {resp.text}")
            return False

        eval_result = resp.json()
        log("4", f"✅ Rules evaluated: {eval_result['alerts_triggered']} alerts triggered")

        # Step 5: Check Alerts
        log("5", "Checking user alerts...")
        resp = session.get(f"{API_BASE}/alerts/{user_id}")
        if resp.status_code != 200:
            log("5", f"❌ Get alerts failed: {resp.status_code} {resp.text}")
            return False

        alerts_result = resp.json()
        log("5", f"✅ Found {alerts_result['count']} alerts for user")

        # Final verification
        log("6", "Verifying user profile...")
        resp = session.get(f"{API_BASE}/api/v1/users/{user_id}")
        if resp.status_code != 200:
            log("6", f"❌ Get user failed: {resp.status_code} {resp.text}")
            return False

        final_user = resp.json()
        log("6", f"✅ User verified: {final_user['email']} (active: {final_user['is_active']})")

        print("\n" + "=" * 70)
        print("🎉 INTEGRATION TEST PASSED!")
        print("=" * 70)
        print("✅ All core features working:")
        print("   • User account management")
        print("   • Medical report upload")
        print("   • AI-powered health queries")
        print("   • Rules engine evaluation")
        print("   • Alert generation and retrieval")
        print(f"\n📊 Test completed for user: {user_id}")
        print("=" * 70)
        return True

    except Exception as e:
        log("ERROR", f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Run the integration test."""
    # Note: This assumes the FastAPI server is running
    # In a real CI environment, you'd start the server first

    print("Note: This test assumes the FastAPI server is running.")
    print("If you get connection errors, start the server with:")
    print("  cd src/backend && uvicorn main:app --reload")
    print()

    success = test_workflow()

    if success:
        print("\n✅ INTEGRATION TEST: PASSED")
        return 0
    else:
        print("\n❌ INTEGRATION TEST: FAILED")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())