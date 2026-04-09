# Detailed Test Cases

This document expands the spreadsheet version in `test-cases.csv`.

For each case, the same core fields from the spreadsheet are preserved, and the source README is listed so you can trace why the case exists.

---

## TC-01

- Source README(s): 1
- No. ID: `TC-01`
- Related Use case: Auth registration success
- Pre-conditions: FastAPI backend running; Supabase Auth and `public.users` mirror logic configured.
- Test Description (steps):
  1. Send `POST /auth/register` with valid name, email, and password.
  2. Capture the response token payload.
  3. Verify the same user exists in both Supabase Auth and `public.users`.
- Expected Outcome: `201 Created` is returned with valid auth tokens or session payload, and the profile row is mirrored successfully so the account can immediately continue in the app.

## TC-02

- Source README(s): 1
- No. ID: `TC-02`
- Related Use case: Auth registration rollback on profile mirror failure
- Pre-conditions: Backend running; a test fixture or DB constraint can force `public.users` insert failure after auth creation.
- Test Description (steps):
  1. Trigger `POST /auth/register` with data that causes the public profile insert to fail.
  2. Inspect the error returned by the API.
  3. Attempt a second registration or login with the same email.
- Expected Outcome: The backend rolls back the auth footprint cleanly; the user is not left in a half-created state and can retry registration later.

## TC-03

- Source README(s): 1
- No. ID: `TC-03`
- Related Use case: Auth login success and `last_login_at` update
- Pre-conditions: Registered user exists; backend and Supabase available.
- Test Description (steps):
  1. Send `POST /auth/login` with valid credentials.
  2. Verify token payload is returned.
  3. Inspect the `users.last_login_at` field for that account.
- Expected Outcome: Login succeeds, tokens are returned, and `last_login_at` is updated as documented.

## TC-04

- Source README(s): 1
- No. ID: `TC-04`
- Related Use case: Auth login invalid credentials
- Pre-conditions: Registered user exists; backend running.
- Test Description (steps):
  1. Call `POST /auth/login` with the wrong password.
  2. Inspect the returned status and error body.
  3. Confirm no valid session data is issued.
- Expected Outcome: The API rejects the login attempt with a safe auth/client error and does not issue tokens.

## TC-05

- Source README(s): 1, 3, 4
- No. ID: `TC-05`
- Related Use case: Protected report upload success
- Pre-conditions: Valid JWT bearer token available; Supabase storage bucket configured.
- Test Description (steps):
  1. Send the report upload request with `user_id` and a valid PDF.
  2. Capture `path` and `public_url`.
  3. Verify the object is physically stored in the correct bucket path.
- Expected Outcome: Upload succeeds and returns storage metadata that can be used by downstream OCR and citation flows.

## TC-06

- Source README(s): 1
- No. ID: `TC-06`
- Related Use case: Protected report upload rejects unauthenticated request
- Pre-conditions: Backend running without a valid bearer token.
- Test Description (steps):
  1. Call the protected upload endpoint with no token or an invalid token.
  2. Inspect the response status.
  3. Verify no object was written to storage.
- Expected Outcome: The backend returns `401` or `403`, and no storage side effects occur.

## TC-07

- Source README(s): 1
- No. ID: `TC-07`
- Related Use case: Async ingestion accepted immediately
- Pre-conditions: OCR and Gemini dependencies configured; valid user and report file available.
- Test Description (steps):
  1. Send `POST /reports/ingest`.
  2. Capture the immediate response and timing.
  3. Store the returned `report_id`.
- Expected Outcome: The endpoint returns `202 Accepted` quickly and starts the rest of the pipeline in the background.

## TC-08

- Source README(s): 1
- No. ID: `TC-08`
- Related Use case: Report listing pagination and newest-first sorting
- Pre-conditions: User has multiple uploaded reports with different timestamps.
- Test Description (steps):
  1. Call `GET /reports` with page parameters.
  2. Verify all returned rows belong to the authenticated user.
  3. Confirm newest-first ordering.
- Expected Outcome: Report listing is paginated correctly and sorted from newest to oldest.

## TC-09

- Source README(s): 1
- No. ID: `TC-09`
- Related Use case: Report status lifecycle tracking
- Pre-conditions: An ingest job is in progress or recently completed.
- Test Description (steps):
  1. Poll `GET /reports/status/{report_id}` after ingestion starts.
  2. Observe intermediate states.
  3. Continue until a terminal state is reached.
- Expected Outcome: The status value follows the documented processing lifecycle and exposes completion or failure clearly.

## TC-10

- Source README(s): 1, 4
- No. ID: `TC-10`
- Related Use case: Synchronous report processing success
- Pre-conditions: Backend running; OCR and Gemini configured; valid file and user available.
- Test Description (steps):
  1. Send `POST /reports/process` with multipart data.
  2. Wait for the full response.
  3. Inspect OCR preview, extraction fields, and identifiers.
- Expected Outcome: The endpoint completes upload, OCR, and extraction in one request and returns a full process payload.

## TC-11

- Source README(s): 1
- No. ID: `TC-11`
- Related Use case: OCR on stored report succeeds and persists text
- Pre-conditions: An uploaded report already exists for the user.
- Test Description (steps):
  1. Call `POST /reports/ocr` with valid `user_id` and `report_id`.
  2. Capture OCR text and confidence values.
  3. Confirm the `medical_reports` row was updated.
- Expected Outcome: OCR output is persisted successfully and is available for retrieval or extraction.

## TC-12

- Source README(s): 1
- No. ID: `TC-12`
- Related Use case: OCR rejects invalid report or mismatched user
- Pre-conditions: Invalid `report_id` or cross-user report reference prepared.
- Test Description (steps):
  1. Call `POST /reports/ocr` with invalid or unauthorized identifiers.
  2. Inspect the error response.
  3. Confirm no downstream updates are written.
- Expected Outcome: The request fails safely and does not create OCR text or partial records.

## TC-13

- Source README(s): 1
- No. ID: `TC-13`
- Related Use case: Gemini lab extraction success with normalization and idempotent replace
- Pre-conditions: OCR text already exists for the report; Gemini is configured.
- Test Description (steps):
  1. Call `POST /reports/extract-labs-gemini`.
  2. Inspect inserted `lab_results`.
  3. Re-run the same extraction for the same report.
- Expected Outcome: Extraction succeeds, normalized results are inserted, and the second run replaces prior rows instead of duplicating them.

## TC-14

- Source README(s): 1
- No. ID: `TC-14`
- Related Use case: Gemini extraction failure path with retries and no partial insert
- Pre-conditions: Test fixture or environment can force Gemini failure or unusable output.
- Test Description (steps):
  1. Trigger extraction on a report that causes Gemini to fail.
  2. Observe retry behavior.
  3. Inspect the database for partial inserts.
- Expected Outcome: The service retries up to the documented limit, reports failure clearly, and leaves no partial lab rows behind.

## TC-15

- Source README(s): 1
- No. ID: `TC-15`
- Related Use case: Alert evaluation success and idempotent replacement
- Pre-conditions: User has `lab_results` that trigger one or more rules.
- Test Description (steps):
  1. Send `POST /alerts/evaluate/{user_id}`.
  2. Inspect created alerts and evidence.
  3. Run the same evaluation again.
- Expected Outcome: Alert generation succeeds and a repeat run replaces prior outputs rather than duplicating them.

## TC-16

- Source README(s): 1, 4
- No. ID: `TC-16`
- Related Use case: Alert retrieval returns explainable evidence
- Pre-conditions: Alerts already exist for the user.
- Test Description (steps):
  1. Call `GET /alerts/{user_id}`.
  2. Inspect each alert's severity, message, and evidence object.
  3. Match evidence back to known lab results or context.
- Expected Outcome: Returned alerts are explainable and traceable to the data that triggered them.

## TC-17

- Source README(s): 1
- No. ID: `TC-17`
- Related Use case: Rules engine threshold-to-severity mapping
- Pre-conditions: Rule fixtures exist near the documented threshold boundaries.
- Test Description (steps):
  1. Evaluate sample values for low, medium, and high thresholds.
  2. Compare each result against the documented rule table.
  3. Repeat for multiple rules.
- Expected Outcome: Severity mapping exactly follows the deterministic rule definitions.

## TC-18

- Source README(s): 1, 3
- No. ID: `TC-18`
- Related Use case: Environment-aware rule escalation
- Pre-conditions: Base alert trigger exists; environmental AQI or temperature threshold is exceeded.
- Test Description (steps):
  1. Evaluate rules with triggering lab values only.
  2. Re-evaluate with qualifying environment data.
  3. Compare severities and reasoning text.
- Expected Outcome: Severity is escalated or advisory text added exactly as documented, with environmental evidence persisted alongside the alert.

## TC-19

- Source README(s): 2
- No. ID: `TC-19`
- Related Use case: OCR text cleaning removes boilerplate conservatively
- Pre-conditions: Sample OCR text includes headers, footers, page markers, and valid medical values.
- Test Description (steps):
  1. Run the cleaning pipeline.
  2. Inspect the cleaned text.
  3. Confirm noise is removed without stripping medical content.
- Expected Outcome: Boilerplate is removed conservatively while key test values, units, and clinically useful text remain.

## TC-20

- Source README(s): 2
- No. ID: `TC-20`
- Related Use case: Chunking preserves measurement rows as standalone evidence units
- Pre-conditions: Clean OCR text contains both measurement rows and narrative text.
- Test Description (steps):
  1. Run the chunking entry point.
  2. Inspect the resulting chunk list.
  3. Verify measurement lines are not mixed into unrelated narrative chunks.
- Expected Outcome: Measurement rows remain intact as individual evidence chunks suitable for RAG citations.

## TC-21

- Source README(s): 2, 3, 4
- No. ID: `TC-21`
- Related Use case: Retrieved chunks include citation metadata
- Pre-conditions: Retrieval metadata migration applied or backfill behavior available.
- Test Description (steps):
  1. Run a retrieval query through pgvector or FAISS.
  2. Inspect each returned chunk object.
  3. Verify `source_filename`, `source_url`, and `page_number` handling.
- Expected Outcome: Retrieval output conforms to the citation-aware contract and exposes metadata needed for UI citations.

## TC-22

- Source README(s): 2
- No. ID: `TC-22`
- Related Use case: Section-label filtering and stable top-k ordering
- Pre-conditions: Chunks have section metadata and retrieval filtering is enabled.
- Test Description (steps):
  1. Run a baseline retrieval.
  2. Run the same query with a section filter.
  3. Compare ordering and top-k behavior.
- Expected Outcome: Section filtering narrows the result set appropriately without breaking relevance ordering.

## TC-23

- Source README(s): 2
- No. ID: `TC-23`
- Related Use case: Structured retrieval logging captures latency phases
- Pre-conditions: Week-4 retrieval logging enabled.
- Test Description (steps):
  1. Execute a retrieval query.
  2. Inspect logs.
  3. Verify request identifiers and phase timings are present.
- Expected Outcome: Logs contain the documented observability fields for retrieval timing and diagnosis.

## TC-24

- Source README(s): 2, 3
- No. ID: `TC-24`
- Related Use case: FAISS retrieval fallback when pgvector is unavailable
- Pre-conditions: Indexed embeddings exist; pgvector path unavailable or disabled.
- Test Description (steps):
  1. Run retrieval using the FAISS strategy.
  2. Inspect result shape and rankings.
  3. Confirm the caller does not need special-case handling.
- Expected Outcome: Retrieval still succeeds with the same response structure through the FAISS fallback path.

## TC-25

- Source README(s): 3
- No. ID: `TC-25`
- Related Use case: Context schema required-field validation
- Pre-conditions: Schema contract and context builder available.
- Test Description (steps):
  1. Build a context missing a required field.
  2. Validate it against the schema.
  3. Repeat with a complete payload.
- Expected Outcome: Invalid payloads fail schema validation and valid payloads pass.

## TC-26

- Source README(s): 3
- No. ID: `TC-26`
- Related Use case: Context builder size controls
- Pre-conditions: Retrieval chunks exceed the documented size constraints.
- Test Description (steps):
  1. Supply more than 10 chunks or oversized chunks to the builder.
  2. Build context.
  3. Measure retained chunk count and total size.
- Expected Outcome: The builder enforces max chunk count and size budgets before LLM use.

## TC-27

- Source README(s): 3, 4
- No. ID: `TC-27`
- Related Use case: RAG query success for user role with grounding
- Pre-conditions: Retrieval data exists; Gemini configured.
- Test Description (steps):
  1. Send `POST /api/v1/rag_query` with `role=user`.
  2. Inspect answer, `grounding_available`, and `chunks_retrieved`.
  3. Check citation style in the returned answer.
- Expected Outcome: The API returns a grounded, user-facing answer with the expected response contract fields.

## TC-28

- Source README(s): 3
- No. ID: `TC-28`
- Related Use case: RAG query success for doctor role with stricter citations
- Pre-conditions: Retrieval data exists; Gemini configured.
- Test Description (steps):
  1. Send `POST /api/v1/rag_query` with `role=doctor`.
  2. Inspect answer format and citations.
  3. Compare with the user-role output.
- Expected Outcome: Doctor responses remain grounded but expose stronger citation detail suitable for clinical traceability.

## TC-29

- Source README(s): 3
- No. ID: `TC-29`
- Related Use case: RAG query rejects invalid query text
- Pre-conditions: Request validation enabled on the route.
- Test Description (steps):
  1. Submit empty, whitespace-only, and too-short queries.
  2. Inspect response status codes.
  3. Confirm no full retrieval/LLM work is performed.
- Expected Outcome: Invalid queries are rejected with `422` before the expensive pipeline starts.

## TC-30

- Source README(s): 3
- No. ID: `TC-30`
- Related Use case: Gemini failure returns fallback answer without breaking the API
- Pre-conditions: Gemini call can be forced to fail or return blocked/empty content.
- Test Description (steps):
  1. Trigger `POST /api/v1/rag_query` under Gemini failure conditions.
  2. Inspect the returned body.
  3. Verify the UI could still render the context.
- Expected Outcome: The API still returns `200` with a fallback answer and a populated `llm_error` field.

## TC-31

- Source README(s): 3
- No. ID: `TC-31`
- Related Use case: Environment snapshot resolution and cache invalidation
- Pre-conditions: Cached environment row exists and coordinate-aware invalidation logic is enabled.
- Test Description (steps):
  1. Query with coordinates close to the cached coordinates.
  2. Query again with materially different coordinates or a conflicting city.
  3. Compare the chosen environment snapshot.
- Expected Outcome: Safe cache reuse occurs for nearby requests, while stale or mismatched location data is invalidated instead of reused.

## TC-32

- Source README(s): 3
- No. ID: `TC-32`
- Related Use case: Prompt safety when environment data is missing
- Pre-conditions: No valid environment snapshot is available for the request.
- Test Description (steps):
  1. Send an environment-aware RAG request without usable environment data.
  2. Inspect the answer text.
  3. Confirm no guessed AQI or weather facts appear.
- Expected Outcome: The assistant explicitly avoids guessing local environmental conditions when the environment block is null or absent.

## TC-33

- Source README(s): 3, 4
- No. ID: `TC-33`
- Related Use case: Wearable vitals ingestion success
- Pre-conditions: Wearable ingestion endpoint active; valid vitals payload available.
- Test Description (steps):
  1. Send `POST /api/v1/ingest/vitals`.
  2. Inspect persisted vitals rows.
  3. Re-submit if idempotency or dedupe behavior is expected.
- Expected Outcome: Wearable vitals are stored correctly for the target user without corrupting the time series.

## TC-34

- Source README(s): 3, 4
- No. ID: `TC-34`
- Related Use case: Wearable vitals summary and reminder computation
- Pre-conditions: User has enough wearable history for summary generation.
- Test Description (steps):
  1. Call `GET /api/v1/vitals/{user_id}/summary`.
  2. Inspect trends, summary fields, and reminders.
  3. Compare with the underlying data.
- Expected Outcome: The summary output is coherent, user-specific, and grounded in the stored wearable signals.

## TC-35

- Source README(s): 3
- No. ID: `TC-35`
- Related Use case: Automated data retention policy enforcement
- Pre-conditions: Cleanup jobs configured; expired environmental and wearable rows exist.
- Test Description (steps):
  1. Seed expired and non-expired rows.
  2. Run the retention cleanup.
  3. Verify which rows remain.
- Expected Outcome: Old environment data older than 3 days and old wearable data older than 30 days are removed while valid current data remains.

## TC-36

- Source README(s): 4
- No. ID: `TC-36`
- Related Use case: Dashboard endpoint full success response
- Pre-conditions: User has dashboard-ready data or the mock server is running.
- Test Description (steps):
  1. Call `GET /api/v1/dashboard/{user_id}`.
  2. Inspect `status`, user data, score, trend, alerts count, and environment block.
  3. Compare response against the contract.
- Expected Outcome: A contract-compliant success payload is returned with the expected dashboard fields.

## TC-37

- Source README(s): 4
- No. ID: `TC-37`
- Related Use case: Dashboard partial-success and zero-state handling
- Pre-conditions: Partial-data or no-data dashboard scenario available.
- Test Description (steps):
  1. Request dashboard data for a user missing some optional inputs.
  2. Inspect API payload and, where applicable, UI behavior.
  3. Verify empty/partial sections do not break rendering.
- Expected Outcome: The system handles missing environment or empty report/alert data gracefully using partial or empty-state behavior.

## TC-38

- Source README(s): 4
- No. ID: `TC-38`
- Related Use case: Doctor patients endpoint success and risk-level integrity
- Pre-conditions: Doctor-patient links exist or mock server has sample data.
- Test Description (steps):
  1. Call `GET /api/v1/doctor/patients?doctor_id=...`.
  2. Inspect patient summaries.
  3. Verify risk levels and last-updated timestamps.
- Expected Outcome: The endpoint returns only the doctor's patients and each entry matches the documented schema.

## TC-39

- Source README(s): 4
- No. ID: `TC-39`
- Related Use case: Android adapter maps HTTP and network failures to `ApiResult.Error`
- Pre-conditions: MockWebServer or equivalent adapter tests available.
- Test Description (steps):
  1. Simulate network failure, timeout, malformed response, and HTTP errors.
  2. Observe `HealthApiAdapterImpl` results.
  3. Trace repository and ViewModel handling.
- Expected Outcome: The adapter converts all these failures into structured `ApiResult.Error` responses with useful error text.

## TC-40

- Source README(s): 4
- No. ID: `TC-40`
- Related Use case: Android UiState handling covers loading, error, empty, and success states
- Pre-conditions: ExampleActivity or screen-level tests available.
- Test Description (steps):
  1. Drive Dashboard, Alerts, and Assistant screens through each UiState.
  2. Observe the composables rendered.
  3. Verify retry callbacks where documented.
- Expected Outcome: Each screen handles all supported states exhaustively and shows the intended loading, error, empty, or success UI.

## TC-41

- Source README(s): 4
- No. ID: `TC-41`
- Related Use case: Android report upload flow and timeline prepend
- Pre-conditions: Android app build available; backend `POST /reports/process` reachable.
- Test Description (steps):
  1. Open the Upload tab and select a document.
  2. Toggle AI versus Standard extraction and submit.
  3. Confirm success navigation and dashboard timeline update.
- Expected Outcome: UiState transitions follow the documented flow and the newly processed report is prepended to the report timeline.

## TC-42

- Source README(s): 3, 4
- No. ID: `TC-42`
- Related Use case: Profile update, account deletion, and location-aware user management
- Pre-conditions: Authenticated user exists; profile screens and user CRUD endpoints integrated.
- Test Description (steps):
  1. Update profile information through the profile-management flow.
  2. Verify `PATCH /api/v1/users/{user_id}` persists changes.
  3. Trigger account deletion and confirm tokens are cleared.
  4. Run location-aware behavior with location available and unavailable.
- Expected Outcome: Profile edits persist, deletion clears local auth state and redirects safely, and location-aware flows degrade gracefully when location is absent.
