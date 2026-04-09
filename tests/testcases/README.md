# Test Cases

This folder contains detailed test cases derived from the provided README files. Each test case includes the following fields:

- **No. ID**: Unique identifier for the test case.
- **Use Case**: The feature or functionality being tested.
- **Pre-conditions**: Any conditions that must be met before the test can be executed.
- **Test Description (steps)**: Step-by-step instructions to execute the test.
- **Expected Outcome**: The expected result of the test.
- **R1 Outcome**: Result of the first round of testing.
- **Comments (if test case failed)**: Notes or observations if the test case fails.
- **R2 Outcome**: Result of the second round of testing.
- **Comments (if test case failed)**: Notes or observations if the test case fails.

## Test Case Details

### Test Case 1
- **No. ID**: TC-01
- **Use Case**: Verify the health check endpoint.
- **Pre-conditions**: FastAPI server is running.
- **Test Description (steps)**:
  1. Send a GET request to the `/health` endpoint.
  2. Verify the response status code is 200.
  3. Verify the response body contains a JSON object with a `status` key and value `ok`.
- **Expected Outcome**: The response status code is 200, and the response body contains `{ "status": "ok" }`.

### Test Case 2
- **No. ID**: TC-02
- **Use Case**: Upload a medical report with a missing user ID.
- **Pre-conditions**: SUPABASE URL and API server running.
- **Test Description (steps)**:
  1. Send a POST request to `/reports/upload` with a multipart form containing a valid file but no user ID.
  2. Verify the response status code is 422.
  3. Verify the response body includes an error message indicating the missing user ID.
- **Expected Outcome**: The response status code is 422, and the error message indicates the missing user ID.

### Test Case 3
- **No. ID**: TC-03
- **Use Case**: Upload a medical report with an empty file.
- **Pre-conditions**: SUPABASE URL and API server running.
- **Test Description (steps)**:
  1. Send a POST request to `/reports/upload` with a multipart form containing an empty file.
  2. Verify the response status code is 400.
  3. Verify the response body includes an error message indicating the file is empty.
- **Expected Outcome**: The response status code is 400, and the error message indicates the file is empty.

### Test Case 4
- **No. ID**: TC-04
- **Use Case**: View uploaded report metadata (empty state).
- **Pre-conditions**: User has uploaded 0 reports.
- **Test Description (steps)**:
  1. Call the `list reports` endpoint or open the `My Reports` page.
  2. Verify the response contains an empty state message.
- **Expected Outcome**: The system returns an empty state message and does not crash.

### Test Case 5
- **No. ID**: TC-05
- **Use Case**: Run OCR on a stored report (PDF heavy path).
- **Pre-conditions**: Tesseract + Poppler installed; API server running.
- **Test Description (steps)**:
  1. Send a POST request to `/reports/ocr` with `user_id` and `report_id`.
  2. Verify the response status code is 200.
  3. Verify the OCR text is extracted and returned in the response.
- **Expected Outcome**: The OCR text is extracted and returned successfully without errors.

... (Additional test cases can be added following this format)