import os
import sys
import time
import uuid
import json
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
UPLOAD_URL = f"{BASE_URL}/reports/upload"
OCR_URL = f"{BASE_URL}/reports/ocr"
EXTRACT_LABS_URL = f"{BASE_URL}/reports/extract-labs"
EXTRACT_LABS_GEMINI_URL = f"{BASE_URL}/reports/extract-labs-gemini"
PROCESS_URL = f"{BASE_URL}/reports/process"

FILE_PATH = os.getenv("REPORT_FILE", "./ocr2/WM17S.pdf")
USER_ID = os.getenv("USER_ID", str(uuid.uuid4()))


def run_step_by_step_test() -> None:
    """Test the step-by-step pipeline: upload → OCR → Gemini extract."""
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"Report file not found: {FILE_PATH}")

    print(f"Using user_id: {USER_ID}")
    print(f"Uploading report: {FILE_PATH}")

    with open(FILE_PATH, "rb") as file_handle:
        response = requests.post(
            UPLOAD_URL,
            data={"user_id": USER_ID},
            files={"file": file_handle},
        )

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Upload failed: {response.status_code} {response.text}")

    payload = response.json()
    storage_path = payload.get("path")
    if not storage_path:
        raise RuntimeError(f"Upload response missing path: {payload}")

    print(f"Uploaded to: {storage_path}")
    time.sleep(1)

    print("Running OCR...")
    response = requests.post(
        OCR_URL,
        data={"user_id": USER_ID, "storage_path": storage_path},
    )

    if response.status_code != 200:
        raise RuntimeError(f"OCR failed: {response.status_code} {response.text}")

    ocr_payload = response.json()
    report_id = ocr_payload.get("report_id")
    print("OCR completed.")
    print(f"Report ID: {report_id}")
    print(f"Confidence: {ocr_payload.get('confidence')}")
    print("OCR text preview:")
    print((ocr_payload.get("ocr_text") or "").strip()[:800])

    if not report_id:
        raise RuntimeError("OCR response missing report_id; cannot extract labs.")

    # --- Gemini extraction ---
    print("\n" + "=" * 60)
    print("Extracting lab results with Gemini AI...")
    print("=" * 60)
    response = requests.post(
        EXTRACT_LABS_GEMINI_URL,
        data={"report_id": report_id},
    )

    if response.status_code != 200:
        print(f"Gemini extraction failed: {response.status_code} {response.text}")
        print("Falling back to regex extraction...")
        response = requests.post(
            EXTRACT_LABS_URL,
            data={"report_id": report_id},
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Regex extraction also failed: {response.status_code} {response.text}"
            )
        extraction_payload = response.json()
        print(f"Regex extraction — lab rows inserted: {extraction_payload.get('inserted')}")
    else:
        extraction_payload = response.json()
        print(json.dumps(extraction_payload, indent=2))
        print(f"\nLab rows inserted: {extraction_payload.get('inserted')}")
        print(f"Lab rows skipped:  {extraction_payload.get('skipped')}")


def run_full_pipeline_test() -> None:
    """Test the single-call full pipeline: process endpoint."""
    if not os.path.exists(FILE_PATH):
        raise FileNotFoundError(f"Report file not found: {FILE_PATH}")

    print(f"\n{'=' * 60}")
    print("FULL PIPELINE TEST (single endpoint)")
    print(f"{'=' * 60}")
    print(f"Using user_id: {USER_ID}")
    print(f"Processing report: {FILE_PATH}")

    with open(FILE_PATH, "rb") as file_handle:
        response = requests.post(
            PROCESS_URL,
            data={"user_id": USER_ID},
            files={"file": file_handle},
        )

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Process failed: {response.status_code} {response.text}")

    result = response.json()
    print(json.dumps(result, indent=2))
    print(f"\nReport ID:      {result.get('report_id')}")
    print(f"OCR Confidence: {result.get('ocr_confidence')}")
    extraction = result.get("extraction", {})
    print(f"Labs inserted:  {extraction.get('inserted', 'N/A')}")
    print(f"Labs skipped:   {extraction.get('skipped', 'N/A')}")
    if result.get("extraction_error"):
        print(f"Extraction error: {result['extraction_error']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "steps"
    try:
        if mode == "full":
            run_full_pipeline_test()
        else:
            run_step_by_step_test()
    except Exception as exc:
        print(f"Verification failed: {exc}")
        sys.exit(1)
