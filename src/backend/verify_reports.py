import os
import sys
import time
import uuid
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
UPLOAD_URL = f"{BASE_URL}/reports/upload"
OCR_URL = f"{BASE_URL}/reports/ocr"
EXTRACT_LABS_URL = f"{BASE_URL}/reports/extract-labs"

FILE_PATH = os.getenv("REPORT_FILE", "./ocr2/WM17S.pdf")
USER_ID = os.getenv("USER_ID", str(uuid.uuid4()))


def run_test() -> None:
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

    print("Extracting lab results...")
    response = requests.post(
        EXTRACT_LABS_URL,
        data={"report_id": report_id},
    )

    if response.status_code != 200:
        raise RuntimeError(f"Lab extraction failed: {response.status_code} {response.text}")

    extraction_payload = response.json()
    print(f"Lab rows inserted: {extraction_payload.get('inserted')}")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as exc:
        print(f"Verification failed: {exc}")
        sys.exit(1)
