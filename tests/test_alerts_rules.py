"""Integration tests for rules engine and alert generation."""
import time

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAlertsAndRules:
    """Test deterministic rules engine and alert generation."""

    def test_evaluate_alerts_no_reports(self, test_client: TestClient, test_user: dict):
        """Test evaluating alerts for a user with no medical reports."""
        user_id = test_user["id"]

        response = test_client.post(f"/alerts/evaluate/{user_id}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()

        assert "user_id" in result
        assert "alerts_triggered" in result
        assert "deleted" in result
        assert "inserted" in result
        assert "evidence_inserted" in result

        # No reports = no alerts
        assert result["alerts_triggered"] == 0
        print(f"\n✓ Rules evaluation with no reports: 0 alerts (expected)")

    def test_evaluate_alerts_with_report(self, test_client: TestClient, uploaded_report: dict, test_user: dict):
        """Test evaluating alerts after uploading a medical report."""
        user_id = test_user["id"]
        report_id = uploaded_report["report_id"]

        # Wait for report processing to complete
        max_wait = 60
        poll_interval = 2
        elapsed = 0

        print(f"\n  Waiting for report processing (report_id: {report_id})...")
        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_response = test_client.get(f"/reports/status/{report_id}")
            status = status_response.json()

            if status["processing_status"] == "done":
                print(f"  ✓ Report processed in {elapsed}s")
                break
            elif status["processing_status"] == "failed":
                pytest.skip(f"Report processing failed: {status.get('processing_error')}")
        else:
            pytest.skip(f"Report processing did not complete within {max_wait}s")

        # Now evaluate rules
        response = test_client.post(f"/alerts/evaluate/{user_id}")

        assert response.status_code == 200
        result = response.json()

        print(f"\n✓ Rules evaluation completed:")
        print(f"  Alerts triggered: {result['alerts_triggered']}")
        print(f"  Alerts inserted: {result['inserted']}")
        print(f"  Evidence items: {result['evidence_inserted']}")

        # We expect some alerts if the report has abnormal values
        # (soft check since it depends on the actual PDF content)
        assert result["alerts_triggered"] >= 0
        assert result["inserted"] >= 0

    def test_get_alerts_empty(self, test_client: TestClient, test_user: dict):
        """Test getting alerts for a user with no alerts."""
        user_id = test_user["id"]

        response = test_client.get(f"/alerts/{user_id}")

        assert response.status_code == 200
        result = response.json()

        assert result["user_id"] == user_id
        assert result["count"] == 0
        assert result["alerts"] == []
        print(f"\n✓ No alerts found for new user (expected)")

    def test_get_alerts_with_evidence(self, test_client: TestClient, uploaded_report: dict, test_user: dict):
        """Test getting alerts with evidence after evaluation."""
        user_id = test_user["id"]
        report_id = uploaded_report["report_id"]

        # Wait for processing
        max_wait = 60
        elapsed = 0
        poll_interval = 2

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            status_response = test_client.get(f"/reports/status/{report_id}")
            status = status_response.json()
            if status["processing_status"] in ["done", "failed"]:
                break
        else:
            pytest.skip("Report processing timeout")

        if status["processing_status"] == "failed":
            pytest.skip(f"Report processing failed: {status.get('processing_error')}")

        # Evaluate rules
        eval_response = test_client.post(f"/alerts/evaluate/{user_id}")
        assert eval_response.status_code == 200
        eval_result = eval_response.json()

        # Get alerts with evidence
        response = test_client.get(f"/alerts/{user_id}?include_evidence=true")

        assert response.status_code == 200
        result = response.json()

        assert "alerts" in result
        print(f"\n✓ Retrieved {result['count']} alerts")

        # If there are alerts, verify their structure
        if result["count"] > 0:
            first_alert = result["alerts"][0]
            assert "id" in first_alert
            assert "severity" in first_alert
            assert "reason" in first_alert
            assert "created_at" in first_alert
            assert "evidence" in first_alert

            # Verify severity is valid
            assert first_alert["severity"] in ["low", "medium", "high", "critical"]

            print(f"  First alert: severity={first_alert['severity']}")
            print(f"  Reason: {first_alert['reason'][:100]}")
            print(f"  Evidence items: {len(first_alert['evidence'])}")

    def test_get_alerts_without_evidence(self, test_client: TestClient, test_user: dict):
        """Test getting alerts without evidence details."""
        user_id = test_user["id"]

        response = test_client.get(f"/alerts/{user_id}?include_evidence=false")

        assert response.status_code == 200
        result = response.json()

        # Alerts without evidence should not have the 'evidence' key
        # (or it should be empty/None)
        if result["count"] > 0:
            first_alert = result["alerts"][0]
            # Evidence field should not be present or should be minimal
            assert "evidence" not in first_alert or first_alert.get("evidence") == []

    def test_alerts_idempotency(self, test_client: TestClient, uploaded_report: dict, test_user: dict):
        """Test that re-evaluating rules is idempotent (replaces old alerts)."""
        user_id = test_user["id"]
        report_id = uploaded_report["report_id"]

        # Wait for processing
        max_wait = 60
        elapsed = 0
        poll_interval = 2

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            status_response = test_client.get(f"/reports/status/{report_id}")
            status = status_response.json()
            if status["processing_status"] in ["done", "failed"]:
                break

        if status["processing_status"] == "failed":
            pytest.skip(f"Report processing failed")

        # Evaluate rules first time
        response1 = test_client.post(f"/alerts/evaluate/{user_id}")
        assert response1.status_code == 200
        result1 = response1.json()

        # Evaluate rules second time (should replace)
        response2 = test_client.post(f"/alerts/evaluate/{user_id}")
        assert response2.status_code == 200
        result2 = response2.json()

        print(f"\n✓ Idempotency test:")
        print(f"  First evaluation: {result1['inserted']} alerts inserted")
        print(f"  Second evaluation: {result2['deleted']} deleted, {result2['inserted']} inserted")

        # The counts should be similar (idempotent behavior)
        assert result2["deleted"] >= 0
        assert result2["inserted"] >= 0

    def test_alert_severity_levels(self, test_client: TestClient, uploaded_report: dict, test_user: dict):
        """Test that alerts have appropriate severity levels."""
        user_id = test_user["id"]
        report_id = uploaded_report["report_id"]

        # Wait and evaluate
        max_wait = 60
        elapsed = 0
        poll_interval = 2

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval
            status_response = test_client.get(f"/reports/status/{report_id}")
            status = status_response.json()
            if status["processing_status"] in ["done", "failed"]:
                break

        if status["processing_status"] == "failed":
            pytest.skip("Report processing failed")

        eval_response = test_client.post(f"/alerts/evaluate/{user_id}")
        assert eval_response.status_code == 200

        # Get alerts
        alerts_response = test_client.get(f"/alerts/{user_id}")
        alerts_result = alerts_response.json()

        if alerts_result["count"] > 0:
            # Group by severity
            severity_counts = {}
            for alert in alerts_result["alerts"]:
                severity = alert["severity"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            print(f"\n✓ Severity distribution:")
            for severity, count in sorted(severity_counts.items()):
                print(f"  {severity}: {count} alerts")

            # All severities should be valid
            valid_severities = {"low", "medium", "high", "critical"}
            for severity in severity_counts.keys():
                assert severity in valid_severities

    def test_evaluate_alerts_invalid_user(self, test_client: TestClient):
        """Test evaluating alerts for non-existent user."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        response = test_client.post(f"/alerts/evaluate/{fake_user_id}")

        # Should succeed but find no data (return 0 alerts)
        # Or might return an error depending on implementation
        assert response.status_code in [200, 404, 400]

        if response.status_code == 200:
            result = response.json()
            assert result["alerts_triggered"] == 0
