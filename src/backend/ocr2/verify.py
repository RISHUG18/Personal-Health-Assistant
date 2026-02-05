import requests
import time
import sys

BASE_URL = "http://localhost:8000"
FILE_PATH = "/home/rishabh/Desktop/sem4/dass/project/project-monorepo-team-48/src/backend/ocr2/WM17S.pdf"

def run_test():
    # 1. Upload
    print("Uploading report...")
    with open(FILE_PATH, "rb") as f:
        response = requests.post(f"{BASE_URL}/upload-report", files={"file": f})
    
    if response.status_code != 200:
        print(f"Upload failed: {response.text}")
        sys.exit(1)
        
    report_id = response.json()["id"]
    print(f"Report ID: {report_id}")
    
    # 2. Run OCR
    print("Running OCR...")
    response = requests.post(f"{BASE_URL}/run-ocr/{report_id}")
    if response.status_code != 200:
        print(f"OCR failed: {response.text}")
        sys.exit(1)
    
    print("OCR Result (Full Text):")
    print(response.text)
    
    # 3. Extract Data (Silent)
    # print("Extracting Medical Data...")
    # response = requests.post(f"{BASE_URL}/extract-medical-data/{report_id}")
    # if response.status_code != 200:
    #     print(f"Extraction failed: {response.text}")
    #     sys.exit(1)
        
    # data = response.json()
    # print("\n--- Extracted Data ---")
    # import json
    # print(json.dumps(data, indent=2))
    
    # 4. Basic Assertion
    # tests = data.get("tests", [])
    # if len(tests) > 0:
    #     print("\nSUCCESS: Extracted tests found.")
    # else:
    #     print("\nWARNING: No tests extracted. Check PDF format or OCR quality.")

if __name__ == "__main__":
    # Wait for server to start if needed
    time.sleep(2)
    try:
        run_test()
    except Exception as e:
        print(f"Test failed: {e}")
