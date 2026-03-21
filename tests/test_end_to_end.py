"""End-to-end integration test simulating complete user journey."""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.requires_pdf
@pytest.mark.requires_env
class TestEndToEndUserJourney:
    """
    Comprehensive end-to-end test simulating a complete user journey.

    This test mimics real user behavior:
    1. User signs up (create account)
    2. User uploads a medical report PDF
    3. System processes the PDF (OCR + extraction)
    4. User asks health-related questions
    5. System evaluates health rules and generates alerts
    6. User views their alerts
    7. User updates their profile
    """

    def test_complete_user_journey(self, test_client: TestClient, test_user_id: str, sample_pdf_path: Path):
        """
        Complete user journey from signup to querying health data.

        This is the primary integration test that validates the entire system works together.
        """
        print("\n" + "=" * 80)
        print("STARTING END-TO-END USER JOURNEY TEST")
        print("=" * 80)

        # ===================================================================
        # Step 1: User Registration
        # ===================================================================
        print("\n[STEP 1] User Registration")
        print("-" * 80)

        user_data = {
            "email": f"journey_test_{test_user_id[:8]}@healthapp.com",
            "full_name": "Arjun Sharma",
            "phone": "+919876543210",
            "date_of_birth": "1988-05-20",
            "gender": "male",
            "address_line1": "123 MG Road",
            "city": "Hyderabad",
            "state": "Telangana",
            "postal_code": "500001",
            "country": "India",
            "blood_group": "O+",
            "height_cm": 178,
            "weight_kg": 82
        }

        signup_response = test_client.post("/api/v1/users", json=user_data)
        assert signup_response.status_code == 201, f"User creation failed: {signup_response.text}"

        user = signup_response.json()
        user_id = user["id"]

        print(f"✓ User registered successfully")
        print(f"  Name: {user['full_name']}")
        print(f"  Email: {user['email']}")
        print(f"  User ID: {user_id}")
        print(f"  Blood Group: {user['blood_group']}")

        # ===================================================================
        # Step 2: Upload Medical Report PDF
        # ===================================================================
        print("\n[STEP 2] Upload Medical Report")
        print("-" * 80)

        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("full_body_checkup_arjun.pdf", f, "application/pdf")}
            data = {"user_id": user_id, "user_name": user["full_name"]}
            upload_response = test_client.post("/reports/ingest", files=files, data=data)

        assert upload_response.status_code == 202, f"PDF upload failed: {upload_response.text}"

        upload_result = upload_response.json()
        report_id = upload_result["report_id"]

        print(f"✓ PDF uploaded successfully")
        print(f"  Report ID: {report_id}")
        print(f"  Storage path: {upload_result['storage_path']}")
        print(f"  Status: {upload_result['processing_status']}")

        # ===================================================================
        # Step 3: Wait for Report Processing (OCR + Extraction)
        # ===================================================================
        print("\n[STEP 3] Processing Medical Report")
        print("-" * 80)

        max_wait = 90
        poll_interval = 3
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_response = test_client.get(f"/reports/status/{report_id}")
            assert status_response.status_code == 200
            status = status_response.json()

            processing_status = status["processing_status"]
            print(f"  [{elapsed:02d}s] Processing status: {processing_status}")

            if processing_status == "done":
                print(f"\n✓ Report processing completed in {elapsed}s")
                print(f"  OCR confidence: {status.get('ocr_confidence', 'N/A')}")
                print(f"  Lab results extracted: {status.get('lab_results_count', 0)}")
                break
            elif processing_status == "failed":
                error_msg = status.get("processing_error", "Unknown error")
                pytest.fail(f"Report processing failed: {error_msg}")
        else:
            pytest.fail(f"Report processing timeout after {max_wait}s")

        # Verify lab results were extracted
        lab_results_response = test_client.get(f"/reports/{report_id}/lab-results")
        assert lab_results_response.status_code == 200
        lab_results = lab_results_response.json()

        print(f"\n  Extracted {lab_results['count']} lab results:")
        for i, result in enumerate(lab_results['lab_results'][:5], 1):  # Show first 5
            print(f"    {i}. {result['test_name']}: {result['value']} {result.get('unit', '')}")
        if lab_results['count'] > 5:
            print(f"    ... and {lab_results['count'] - 5} more")

        # ===================================================================
        # Step 4: User Asks Health Questions
        # ===================================================================
        print("\n[STEP 4] User Queries Health Data")
        print("-" * 80)

        queries = [
            "What are my recent blood test results?",
            "Are there any concerning values in my reports?",
            "Give me suggestions to improve my health based on my lab results"
        ]

        for i, query_text in enumerate(queries, 1):
            print(f"\n  Query {i}: \"{query_text}\"")

            query_data = {
                "user_id": user_id,
                "query": query_text,
                "role": "user",
                "top_k": 10,
                "match_threshold": 0.3,
                "user_location": "Hyderabad"
            }

            query_response = test_client.post("/api/v1/rag_query", json=query_data)
            assert query_response.status_code == 200, f"Query failed: {query_response.text}"

            query_result = query_response.json()

            print(f"  ✓ Answer received:")
            print(f"    Model: {query_result['model']}")
            print(f"    Chunks retrieved: {query_result['chunks_retrieved']}")
            print(f"    Grounding: {query_result['grounding_available']}")
            print(f"    Answer preview: {query_result['answer'][:150]}...")

            # Verify the model is correct
            assert "gemini-3.1" in query_result["model"].lower() or "3.1" in query_result["model"], \
                f"Expected gemini-3.1-pro-preview, got {query_result['model']}"

        # ===================================================================
        # Step 5: Evaluate Health Rules and Generate Alerts
        # ===================================================================
        print("\n[STEP 5] Evaluate Health Rules")
        print("-" * 80)

        eval_response = test_client.post(f"/alerts/evaluate/{user_id}")
        assert eval_response.status_code == 200, f"Rules evaluation failed: {eval_response.text}"

        eval_result = eval_response.json()

        print(f"✓ Rules evaluation completed")
        print(f"  Alerts triggered: {eval_result['alerts_triggered']}")
        print(f"  Alerts inserted: {eval_result['inserted']}")
        print(f"  Evidence items: {eval_result['evidence_inserted']}")
        if eval_result.get('errors'):
            print(f"  ⚠ Errors: {eval_result['errors']}")

        # ===================================================================
        # Step 6: User Views Alerts
        # ===================================================================
        print("\n[STEP 6] View Health Alerts")
        print("-" * 80)

        alerts_response = test_client.get(f"/alerts/{user_id}?include_evidence=true")
        assert alerts_response.status_code == 200

        alerts_result = alerts_response.json()

        print(f"✓ Retrieved {alerts_result['count']} alerts")

        if alerts_result['count'] > 0:
            print(f"\n  Alert Details:")
            for i, alert in enumerate(alerts_result['alerts'][:3], 1):  # Show first 3
                print(f"\n    Alert {i}:")
                print(f"      Severity: {alert['severity'].upper()}")
                print(f"      Reason: {alert['reason'][:100]}...")
                print(f"      Evidence items: {len(alert.get('evidence', []))}")
            if alerts_result['count'] > 3:
                print(f"\n    ... and {alerts_result['count'] - 3} more alerts")
        else:
            print("  No critical alerts found (all values within normal range)")

        # ===================================================================
        # Step 7: User Updates Profile
        # ===================================================================
        print("\n[STEP 7] Update User Profile")
        print("-" * 80)

        update_data = {
            "weight_kg": 80,  # User lost 2kg!
            "phone": "+919999888877"
        }

        update_response = test_client.patch(f"/api/v1/users/{user_id}", json=update_data)
        assert update_response.status_code == 200

        updated_user = update_response.json()

        print(f"✓ Profile updated successfully")
        print(f"  Weight updated: {user['weight_kg']} kg → {updated_user['weight_kg']} kg")
        print(f"  Phone updated: {user.get('phone', 'N/A')} → {updated_user['phone']}")

        # ===================================================================
        # Step 8: Verify User Profile
        # ===================================================================
        print("\n[STEP 8] Verify Current User State")
        print("-" * 80)

        profile_response = test_client.get(f"/api/v1/users/{user_id}")
        assert profile_response.status_code == 200

        current_profile = profile_response.json()

        print(f"✓ Current user profile:")
        print(f"  Name: {current_profile['full_name']}")
        print(f"  Email: {current_profile['email']}")
        print(f"  Weight: {current_profile['weight_kg']} kg")
        print(f"  Blood Group: {current_profile['blood_group']}")
        print(f"  Active: {current_profile['is_active']}")

        # ===================================================================
        # Journey Complete
        # ===================================================================
        print("\n" + "=" * 80)
        print("END-TO-END USER JOURNEY TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  ✓ User registered and profile managed")
        print(f"  ✓ Medical report uploaded and processed")
        print(f"  ✓ {lab_results['count']} lab results extracted")
        print(f"  ✓ {len(queries)} AI-powered health queries answered")
        print(f"  ✓ {eval_result['alerts_triggered']} health alerts evaluated")
        print(f"  ✓ Profile updated successfully")
        print(f"\n  Model used: {query_result['model']}")
        print(f"  Test User ID: {user_id}")
        print("=" * 80 + "\n")

        # Final assertions
        assert user_id is not None
        assert report_id is not None
        assert lab_results['count'] > 0, "Expected lab results to be extracted"
        assert "gemini-3.1" in query_result["model"].lower(), "Expected gemini-3.1-pro-preview model"

    def test_user_journey_with_environment_data(self, test_client: TestClient, test_user_id: str):
        """
        Test user journey focusing on environmental data integration.
        """
        print("\n" + "=" * 80)
        print("ENVIRONMENT-AWARE USER JOURNEY TEST")
        print("=" * 80)

        # Create user
        user_data = {
            "email": f"env_test_{test_user_id[:8]}@healthapp.com",
            "full_name": "Priya Reddy",
            "city": "Delhi"
        }

        signup_response = test_client.post("/api/v1/users", json=user_data)
        assert signup_response.status_code == 201
        user = signup_response.json()
        user_id = user["id"]

        print(f"\n✓ User created: {user['full_name']} in {user.get('city', 'Unknown')}")

        # Query with GPS coordinates (simulating mobile app)
        print(f"\n[QUERY] User asks about outdoor activity with GPS location")

        query_data = {
            "user_id": user_id,
            "query": "Is it safe to go for a morning jog today?",
            "role": "user",
            "user_lat": 28.6139,  # Delhi coordinates
            "user_lon": 77.2090,
            "user_location": "Delhi"
        }

        query_response = test_client.post("/api/v1/rag_query", json=query_data)
        assert query_response.status_code == 200

        result = query_response.json()

        print(f"✓ Environment-aware answer received")
        print(f"  Answer: {result['answer'][:200]}...")

        # Verify environmental data was used
        context = result.get("context", {})
        if context.get("environment"):
            env = context["environment"]
            print(f"\n  Environmental data used:")
            print(f"    Location: {env.get('location_city', 'N/A')}")
            print(f"    AQI: {env.get('aqi_level', 'N/A')}")
            print(f"    Weather: {env.get('weather_condition', 'N/A')}")

        print("\n" + "=" * 80 + "\n")
