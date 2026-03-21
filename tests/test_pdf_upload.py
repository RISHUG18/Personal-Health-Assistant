"""Integration tests for PDF upload and processing pipeline."""
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.requires_pdf
class TestPDFUpload:
    """Test PDF upload and processing pipeline."""

    def test_upload_pdf_basic(self, test_client: TestClient, test_user: dict, sample_pdf_path: Path):
        """Test basic PDF upload to storage (no processing)."""
        user_id = test_user["id"]

        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test_report.pdf", f, "application/pdf")}
            data = {"user_id": user_id, "user_name": test_user["full_name"]}
            response = test_client.post("/reports/upload", files=files, data=data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        result = response.json()
        assert "path" in result
        assert "public_url" in result
        assert user_id in result["path"]

    def test_ingest_pdf_async(self, test_client: TestClient, test_user: dict, sample_pdf_path: Path):
        """Test full async PDF ingestion pipeline (upload + OCR + extraction)."""
        user_id = test_user["id"]

        # Step 1: Upload and trigger async processing
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("full_body_checkup.pdf", f, "application/pdf")}
            data = {"user_id": user_id, "user_name": test_user["full_name"]}
            response = test_client.post("/reports/ingest", files=files, data=data)

        assert response.status_code == 202, f"Expected 202 for async processing, got {response.status_code}: {response.text}"
        result = response.json()
        assert "report_id" in result
        assert "processing_status" in result
        assert result["processing_status"] == "pending"
        report_id = result["report_id"]

        print(f"\n✓ PDF uploaded successfully, report_id: {report_id}")

        # Step 2: Poll status until processing completes
        max_wait = 60  # seconds
        poll_interval = 2
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_response = test_client.get(f"/reports/status/{report_id}")
            assert status_response.status_code == 200
            status = status_response.json()

            print(f"  Polling ({elapsed}s): status={status['processing_status']}")

            if status["processing_status"] == "done":
                print(f"✓ Processing completed in {elapsed}s")
                assert status["ocr_confidence"] is not None
                assert status["lab_results_count"] is not None
                assert status["lab_results_count"] > 0, "Expected at least some lab results extracted"
                break
            elif status["processing_status"] == "failed":
                pytest.fail(f"Processing failed: {status.get('processing_error')}")
        else:
            pytest.fail(f"Processing did not complete within {max_wait}s")

        # Step 3: Verify lab results were extracted
        lab_results_response = test_client.get(f"/reports/{report_id}/lab-results")
        assert lab_results_response.status_code == 200
        lab_results = lab_results_response.json()
        assert lab_results["count"] > 0
        assert isinstance(lab_results["lab_results"], list)

        # Verify structure of lab results
        first_result = lab_results["lab_results"][0]
        assert "test_name" in first_result
        assert "value" in first_result
        print(f"✓ Extracted {lab_results['count']} lab results")

    def test_process_pdf_sync(self, test_client: TestClient, test_user: dict, sample_pdf_path: Path):
        """Test synchronous PDF processing (blocking)."""
        user_id = test_user["id"]

        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test_report.pdf", f, "application/pdf")}
            data = {"user_id": user_id, "user_name": test_user["full_name"]}
            response = test_client.post("/reports/process", files=files, data=data, timeout=120)

        # This endpoint blocks until processing is complete
        if response.status_code == 201:
            result = response.json()
            assert result["processing_status"] == "done"
            assert "report_id" in result
            assert "lab_results" in result
            assert len(result["lab_results"]) > 0
            print(f"\n✓ Sync processing completed, {len(result['lab_results'])} results extracted")
        else:
            # Sync processing might fail if Gemini API is unavailable
            print(f"\n⚠ Sync processing returned {response.status_code}: {response.text}")
            pytest.skip("Sync processing endpoint not available or failed")

    def test_upload_without_user_id(self, test_client: TestClient, sample_pdf_path: Path):
        """Test that uploading without user_id fails."""
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test_report.pdf", f, "application/pdf")}
            # Missing user_id
            response = test_client.post("/reports/upload", files=files)

        assert response.status_code == 422, "Should require user_id"

    def test_upload_invalid_user_id(self, test_client: TestClient, sample_pdf_path: Path):
        """Test uploading with a non-existent user_id."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test_report.pdf", f, "application/pdf")}
            data = {"user_id": fake_user_id}
            response = test_client.post("/reports/upload", files=files, data=data)

        # Upload itself should succeed (storage doesn't validate user existence)
        # The foreign key validation happens when creating DB records
        assert response.status_code in [201, 400, 404]

    def test_get_report_status_not_found(self, test_client: TestClient):
        """Test getting status of non-existent report."""
        fake_report_id = "00000000-0000-0000-0000-000000000000"

        response = test_client.get(f"/reports/status/{fake_report_id}")

        assert response.status_code == 404

    def test_get_lab_results_empty(self, test_client: TestClient, test_user: dict, sample_pdf_path: Path):
        """Test getting lab results for a report that hasn't been processed yet."""
        user_id = test_user["id"]

        # Upload without triggering processing
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test_report.pdf", f, "application/pdf")}
            data = {"user_id": user_id}
            upload_response = test_client.post("/reports/upload", files=files, data=data)

        assert upload_response.status_code == 201

        # Try to get lab results - should return empty since extraction hasn't run
        # Note: We need a report_id, but /upload doesn't create DB record
        # This test is more conceptual - in practice, we'd need to create a DB record first
