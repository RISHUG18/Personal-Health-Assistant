Aditya Singh

# API Contract Definition

## Overview
This document describes the API contract definitions for the Health MVP application, covering:
- Dashboard endpoint
- Alerts endpoint
- RAG/Chat endpoint
- Report upload endpoint
- Doctor patients endpoint

## Functionalities
- Defines OpenAPI 3.0 specification as the single source of truth for all API endpoints
- Provides TypeScript type definitions for frontend integration
- Includes a standalone mock server for immediate UI development and testing
- Covers success cases, partial data cases, and error states for all endpoints

## Files Involved
- [src/backend/contracts/api_spec.yaml](backend/contracts/api_spec.yaml): OpenAPI/Swagger specification (Master Contract)
- [src/types/api.ts](types/api.ts): TypeScript type definitions for frontend components
- [src/backend/mock_server.py](backend/mock_server.py): Standalone mock server for UI testing

---

## API Endpoints

### 1. Dashboard Endpoint
**GET** `/api/v1/dashboard/{user_id}`

Returns high-level metrics, wellbeing score, and active alert counts.

| Response Code | Description |
|---------------|-------------|
| 200 | Successful load with full dashboard data |
| 500 | Server error with error message |

### 2. Alerts Endpoint
**GET** `/api/v1/alerts?user_id={user_id}`

Returns all notifications and alerts with evidence data.

| Response Code | Description |
|---------------|-------------|
| 200 | List of alerts with explainable evidence |

### 3. RAG/Chat Endpoint
**POST** `/api/v1/rag_query`

Ask the AI Coach a question and receive an answer with grounding context.

| Response Code | Description |
|---------------|-------------|
| 200 | AI answer with context, grounding flag, and model info |

### 4. Report Upload Endpoint
**POST** `/reports/upload`

Upload a medical PDF for processing (multipart/form-data).

| Response Code | Description |
|---------------|-------------|
| 201 | Created — returns storage path and public URL |

### 5. Doctor Patients Endpoint
**GET** `/api/v1/doctor/patients?doctor_id={doctor_id}`

Returns list of patients with risk status for doctor view.

| Response Code | Description |
|---------------|-------------|
| 200 | List of patients with risk levels |

---

## Data Schemas

### DashboardResponse
| Field | Type | Description |
|-------|------|-------------|
| status | string | "success", "partial_success", or "error" |
| data.user_id | string | Unique patient ID |
| data.greeting | string | Personalized greeting |
| data.wellbeing_score | integer | Score from 0-100 |
| data.wellbeing_trend | enum | "improving", "stable", or "declining" |
| data.active_alerts_count | integer | Number of active alerts |
| data.environment | object/null | AQI and weather data (nullable for partial data) |

### AlertItem
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique alert ID |
| title | string | Alert title |
| severity | enum | "low", "medium", or "high" |
| timestamp | datetime | When alert was triggered |
| message | string | Alert description |
| evidence | object/null | Explainable data (source, metric, value, threshold) |

### RagResponse
| Field | Type | Description |
|-------|------|-------------|
| answer | string | AI-generated response |
| chunks_retrieved | integer | Number of RAG chunks that passed similarity threshold |
| grounding_available | boolean | True when retrieved_chunks is non-empty |
| model | string | Name of the Gemini model used |
| llm_error | string/null | Non-null only when Gemini failed and fallback answer was used |

### PatientSummary (Doctor View)
| Field | Type | Description |
|-------|------|-------------|
| user_id | string | Patient ID |
| name | string | Patient name |
| age | integer | Patient age |
| risk_level | enum | "low", "medium", or "high" (Traffic Light UI) |
| last_updated | datetime | Last data update timestamp |

---

## Running the Mock Server

### Prerequisites
```bash
pip install fastapi uvicorn python-multipart
```

### Start the Server
```bash
cd src/backend
uvicorn mock_server:app --reload
```

### Test Endpoints
- Dashboard: http://127.0.0.1:8000/api/v1/dashboard/patient_001
- Alerts: http://127.0.0.1:8000/api/v1/alerts?user_id=patient_001
- Doctor Patients: http://127.0.0.1:8000/api/v1/doctor/patients?doctor_id=doc_001
- API Docs: http://127.0.0.1:8000/docs

### Simulating Error States
Use `user_id=error_test` to trigger error responses:
```
http://127.0.0.1:8000/api/v1/dashboard/error_test
```

---

## Flow (Brief)

1. **Frontend Integration**: Import types from `src/types/api.ts` into React/Native components.
2. **Mock Development**: Run `mock_server.py` to get a working "backend" for UI development.
3. **API Contract Reference**: Use `api_spec.yaml` as the single source of truth for team coordination.
4. **Testing**: All endpoints support success, partial data, and error state responses.

---

## Checklist

- [x] User App Specs (Dashboard, Chat, Alerts) - Complete
- [x] Ingestion Specs (Upload) - Complete
- [x] Doctor Specs (Patient List) - Complete
- [x] TypeScript Types - Complete
- [x] Mock Server - Complete
- [x] Android API Adapter Layer - Complete

---
---

# Android API Adapter Layer

## Overview
This document describes the Android API Adapter Layer that connects the Android frontend to real backend endpoints. The adapter provides:
- Clean abstraction over all HTTP communication
- Strongly typed Kotlin data models
- Structured error handling
- MVVM-compatible architecture with Repository pattern

## Architecture

```
UI (Compose) → ViewModel → Repository → API Adapter → Retrofit → Backend
```

The UI layer **never** calls the backend directly. All communication is routed through the adapter layer, which is the single source of truth for network operations.

## Functionalities
- Encapsulates all HTTP requests via Retrofit + OkHttp
- Handles responses and errors with a sealed `ApiResult` class
- Provides strongly typed Kotlinx Serialization models matching the backend contract
- Exposes a Repository layer for ViewModel consumption
- Supports all 5 backend endpoints (Dashboard, Alerts, RAG Query, Report Upload, Doctor Patients)

## Files Involved

### Data Models
- [src/android/app/src/main/java/com/vitalis/health/data/model/Alert.kt](android/app/src/main/java/com/vitalis/health/data/model/Alert.kt): Alert, AlertEvidence, AlertsResponse
- [src/android/app/src/main/java/com/vitalis/health/data/model/Dashboard.kt](android/app/src/main/java/com/vitalis/health/data/model/Dashboard.kt): DashboardData, DashboardResponse, Environment
- [src/android/app/src/main/java/com/vitalis/health/data/model/RagQuery.kt](android/app/src/main/java/com/vitalis/health/data/model/RagQuery.kt): RagQueryRequest, RagData, Citation, RagResponse
- [src/android/app/src/main/java/com/vitalis/health/data/model/Report.kt](android/app/src/main/java/com/vitalis/health/data/model/Report.kt): ReportUploadResponse
- [src/android/app/src/main/java/com/vitalis/health/data/model/Doctor.kt](android/app/src/main/java/com/vitalis/health/data/model/Doctor.kt): Patient, PatientsResponse

### Network Core
- [src/android/app/src/main/java/com/vitalis/health/data/network/ApiResult.kt](android/app/src/main/java/com/vitalis/health/data/network/ApiResult.kt): Sealed class (Success / Error) with utility methods
- [src/android/app/src/main/java/com/vitalis/health/data/network/HealthApiService.kt](android/app/src/main/java/com/vitalis/health/data/network/HealthApiService.kt): Retrofit interface — raw HTTP contract

### API Adapter
- [src/android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapter.kt](android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapter.kt): Adapter interface contract
- [src/android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapterImpl.kt](android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapterImpl.kt): Full implementation with error handling and response mapping

### Repository
- [src/android/app/src/main/java/com/vitalis/health/data/repository/HealthRepository.kt](android/app/src/main/java/com/vitalis/health/data/repository/HealthRepository.kt): Business-logic layer between ViewModels and adapter

### DI / Network Config
- [src/android/app/src/main/java/com/vitalis/health/di/NetworkModule.kt](android/app/src/main/java/com/vitalis/health/di/NetworkModule.kt): OkHttp, Retrofit, Kotlinx Serialization wiring

### Application
- [src/android/app/src/main/java/com/vitalis/health/VitalisApp.kt](android/app/src/main/java/com/vitalis/health/VitalisApp.kt): App singleton that wires the dependency graph

### ViewModels
- [src/android/app/src/main/java/com/vitalis/health/ui/DashboardViewModel.kt](android/app/src/main/java/com/vitalis/health/ui/DashboardViewModel.kt): Dashboard screen state management
- [src/android/app/src/main/java/com/vitalis/health/ui/AlertsViewModel.kt](android/app/src/main/java/com/vitalis/health/ui/AlertsViewModel.kt): Alerts screen state management
- [src/android/app/src/main/java/com/vitalis/health/ui/AssistantViewModel.kt](android/app/src/main/java/com/vitalis/health/ui/AssistantViewModel.kt): AI chat screen state + conversation history
- [src/android/app/src/main/java/com/vitalis/health/ui/ViewModelFactory.kt](android/app/src/main/java/com/vitalis/health/ui/ViewModelFactory.kt): Manual DI factory for ViewModels

### Example UI
- [src/android/app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt](android/app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt): Compose Activity with Dashboard / Alerts / AI Chat tabs

### Tests
- [src/android/app/src/test/java/com/vitalis/health/data/adapter/HealthApiAdapterImplTest.kt](android/app/src/test/java/com/vitalis/health/data/adapter/HealthApiAdapterImplTest.kt): MockWebServer unit tests

### Build Config
- [src/android/app/build.gradle.kts](android/app/build.gradle.kts): Dependencies (Retrofit, OkHttp, Kotlinx Serialization, Compose)
- [src/android/app/src/main/AndroidManifest.xml](android/app/src/main/AndroidManifest.xml): Permissions and launcher activity

---

## Adapter Functions

### 1. Fetch Dashboard
```kotlin
suspend fun fetchDashboard(userId: String): ApiResult<DashboardData>
```
Calls **GET** `/api/v1/dashboard/{user_id}` and returns the parsed `DashboardData` or a structured error.

### 2. Fetch Alerts
```kotlin
suspend fun fetchAlerts(userId: String): ApiResult<List<Alert>>
```
Calls **GET** `/api/v1/alerts?user_id={user_id}` and returns the alert list (sorted by severity in the repository).

### 3. Query Health Assistant (RAG)
```kotlin
suspend fun queryHealthAssistant(userId: String, query: String): ApiResult<RagData>
```
Calls **POST** `/api/v1/rag_query` with a JSON body and returns the AI answer (citations default to empty — real backend embeds them in the deep `context` object).

### 4. Upload Report
```kotlin
suspend fun uploadReport(userId: String, fileName: String, fileBytes: ByteArray): ApiResult<ReportUploadResponse>
```
Calls **POST** `/reports/upload` as multipart/form-data. Returns `{path, public_url}`.

### 5. Fetch Patients (Doctor View)
```kotlin
suspend fun fetchPatients(doctorId: String): ApiResult<List<Patient>>
```
Calls **GET** `/api/v1/doctor/patients?doctor_id={doctor_id}` and returns the patient list.

---

## Error Handling

All adapter methods return `ApiResult<T>`:

```kotlin
sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error(val message: String, val code: Int?, val throwable: Throwable?) : ApiResult<Nothing>()
}
```

| Error Type | Handling |
|---|---|
| Network failure (no connection) | Caught as `IOException` → user-friendly message |
| Timeout | Caught as `SocketTimeoutException` → timeout message |
| HTTP 4xx/5xx | Mapped to descriptive error text per status code |
| Empty/malformed response | Returned as `ApiResult.Error` with details |
| Business-logic error (e.g. `status: "error"`) | Detected in adapter and surfaced as error |

---

## Technical Stack

| Concern | Technology |
|---|---|
| Language | Kotlin |
| Networking | Retrofit 2.9 + OkHttp 4.12 |
| Serialization | Kotlinx Serialization 1.6 |
| Async | Kotlin Coroutines |
| Architecture | MVVM + Clean Architecture |
| UI | Jetpack Compose + Material 3 |
| Testing | JUnit 4 + OkHttp MockWebServer |

---

## Flow (Brief)

1. **UI** observes `ViewModel.uiState` (LiveData) for loading/success/error states.
2. **ViewModel** calls `Repository` methods inside `viewModelScope.launch`.
3. **Repository** delegates to `HealthApiAdapter`, optionally applying business logic (e.g. sorting alerts).
4. **Adapter** calls the Retrofit service, wraps the response in `ApiResult`, and handles all exceptions.
5. **Retrofit + OkHttp** perform the actual HTTP request to the FastAPI backend.

---

## Adapter Layer Checklist

- [x] Retrofit interface with all 5 endpoints
- [x] API Adapter interface + implementation
- [x] Strongly typed data models (Kotlinx Serialization)
- [x] Sealed `ApiResult` with `Success` / `Error`
- [x] Error handling (network, timeout, HTTP codes, malformed responses)
- [x] Repository layer with business logic
- [x] ViewModels for Dashboard, Alerts, AI Assistant
- [x] Example Compose UI with 3 tabs
- [x] MockWebServer unit tests
- [x] Build config with all dependencies

---
---

# Developer Observability — OkHttp Interceptor

## Overview
This section documents the addition of a custom OkHttp interceptor (`VitalisInterceptor`) that provides structured logging and performance monitoring for all network calls made by the Android app.

## Functionalities
- Logs every outgoing request: HTTP method, URL, and truncated request body (≤ 500 chars)
- Logs every incoming response: status code, URL, elapsed time, and truncated response body
- Flags non-2xx responses as `Log.w` warnings so API errors are immediately visible in Logcat
- Flags slow responses exceeding **2 000 ms** with a dedicated `Log.w("VitalisInterceptor", "SLOW REQUEST [Xms]: ...")` entry
- Catches and logs `IOException` failures with `Log.e` before re-throwing, preserving the original call stack
- Reads response body non-destructively (uses buffered peek) so OkHttp can still process the body downstream

## Files Involved
- [src/android/app/src/main/java/com/vitalis/health/di/VitalisInterceptor.kt](android/app/src/main/java/com/vitalis/health/di/VitalisInterceptor.kt): Custom `okhttp3.Interceptor` implementation
- [src/android/app/src/main/java/com/vitalis/health/di/NetworkModule.kt](android/app/src/main/java/com/vitalis/health/di/NetworkModule.kt): Updated `provideOkHttpClient()` to register `VitalisInterceptor` before `HttpLoggingInterceptor`

## Flow (Brief)
1. Every HTTP call passes through `VitalisInterceptor` first (before OkHttp's own logging interceptor).
2. The interceptor logs the request, records the start timestamp, and calls `chain.proceed()`.
3. On response, it calculates elapsed time and decides whether to emit a SLOW REQUEST warning.
4. Non-2xx status codes are logged as warnings for quick triage in Logcat.
5. `HttpLoggingInterceptor` (already present) still runs after `VitalisInterceptor` for full raw body dumps.

## Checklist
- [x] `VitalisInterceptor.kt` created in `com.vitalis.health.di`
- [x] Request logging (method, URL, body snippet)
- [x] Response logging (status code, URL, elapsed time, body snippet)
- [x] Non-2xx response warnings
- [x] Slow response threshold flag (> 2 000 ms)
- [x] `IOException` error logging
- [x] Wired into `NetworkModule.provideOkHttpClient()` as first interceptor

---
---

# Compose Design System — VitalisTheme

## Overview
This section documents the extraction of the design system from `src/frontend/sample.html` and its translation into a reusable Jetpack Compose Material 3 theme (`VitalisTheme`).

## Functionalities
- Defines all color tokens from the HTML prototype (`--primary`, `--bg-app`, `--danger`, etc.) as named Kotlin `Color` constants
- Provides full `lightColorScheme` and `darkColorScheme` mapped to Material 3 roles
- Defines `VitalisTypography` using DM Sans across all text styles (with graceful fallback to the system default font if font assets are not yet bundled) and `MetricTextStyle` in IBM Plex Mono for numeric health values
- Defines `VitalisShapes` with corner radii matching the HTML: 6 dp / 10 dp / 14 dp / 18 dp / 24 dp
- Exposes a `VitalisTheme { }` composable wrapper that replaces the generic `MaterialTheme { }` used previously

## Files Involved
- [src/android/app/src/main/java/com/vitalis/health/ui/theme/VitalisTheme.kt](android/app/src/main/java/com/vitalis/health/ui/theme/VitalisTheme.kt): Color constants, color schemes, typography, shapes, and theme composable
- [src/frontend/sample.html](frontend/sample.html): Source design reference (CSS custom properties)

## Design Tokens (from HTML → Compose)

| HTML variable | Kotlin constant | Value |
|---|---|---|
| `--primary` | `VitalisPrimary` | `#10785A` |
| `--primary-dark` | `VitalisPrimaryDark` | `#0B5E46` |
| `--primary-light` | `VitalisPrimaryLight` | `#E8F5F0` |
| `--primary-muted` | `VitalisPrimaryMuted` | `#B4D7CC` |
| `--bg-app` | `VitalisBgApp` | `#F5F7F6` |
| `--bg-card` | `VitalisBgCard` | `#FFFFFF` |
| `--text-primary` | `VitalisTextPrimary` | `#1A2B25` |
| `--text-secondary` | `VitalisTextSecondary` | `#506B60` |
| `--text-muted` | `VitalisTextMuted` | `#8FA69B` |
| `--warning` | `VitalisWarning` | `#C27817` |
| `--danger` | `VitalisDanger` | `#C0392B` |
| `--success` | `VitalisSuccess` | `#1E7D5A` |
| `--border` | `VitalisBorder` | `#DAE3DE` |

## Checklist
- [x] All HTML color tokens mapped to named Kotlin `Color` constants
- [x] `lightColorScheme` covering all Material 3 roles
- [x] `darkColorScheme` with appropriate dark-mode tints
- [x] `VitalisTypography` — DM Sans for all body/label/title/headline/display styles
- [x] `MetricTextStyle` — IBM Plex Mono for score and lab value display
- [x] `VitalisShapes` — 6 / 10 / 14 / 18 / 24 dp radii
- [x] `VitalisTheme` composable wrapper
- [x] `ExampleActivity` switched from `MaterialTheme` to `VitalisTheme`

---
---

# Shared UiState Composables

## Overview
This section documents the creation of a shared library of stateful screen composables that mirror the loading, error, and empty-state patterns established in the HTML prototype.

## Functionalities
- `VitalisLoadingScreen(label)` — full-screen centered `CircularProgressIndicator` (green, 3 dp stroke) with optional descriptive label; maps to the HTML `.loading-spinner` pattern
- `VitalisErrorScreen(message, title, onRetry)` — full-screen error card using `MaterialTheme.colorScheme.errorContainer`, red icon, and an optional retry `Button` styled with `VitalisPrimary`; maps to the HTML `.alert-card.high-priority` red left-border pattern
- `VitalisEmptyScreen(message, icon, subtitle)` — full-screen centered icon + muted text block; maps to the HTML `.chat-home-welcome` idle state

## Files Involved
- [src/android/app/src/main/java/com/vitalis/health/ui/components/StateScreens.kt](android/app/src/main/java/com/vitalis/health/ui/components/StateScreens.kt): All three shared state composables

## Flow (Brief)
1. A screen composable observes a `ViewModel`'s `LiveData<UiState>` via `observeAsState()`.
2. The `when` branch delegates to the appropriate shared composable for non-content states.
3. Only the `Success` branch renders actual data content.
4. The `onRetry` lambda on `VitalisErrorScreen` re-triggers the ViewModel's load function.

## Checklist
- [x] `VitalisLoadingScreen` with branded spinner and optional label
- [x] `VitalisErrorScreen` with error card, icon, and retry button
- [x] `VitalisEmptyScreen` with configurable icon, message, and subtitle
- [x] All composables use `VitalisTheme` color roles (no hardcoded colors)

---
---

# Exhaustive UiState Handling in ExampleActivity

## Overview
This section documents the updates made to `ExampleActivity` to exhaustively handle every possible `UiState` across all three tabs (Dashboard, Alerts, AI Assistant), replacing the minimal placeholder states that existed before.

## Functionalities
- `MaterialTheme` replaced with `VitalisTheme` so the entire Activity uses the design system
- Bottom navigation bar items now include descriptive `Icon` composables (SpaceDashboard, Notifications, Forum) alongside their labels
- `DashboardScreen` handles: `Loading → VitalisLoadingScreen` | `Error → VitalisErrorScreen(onRetry)` | `Success → DashboardContent` | `null → VitalisEmptyScreen`
- `AlertsScreen` handles: `Loading → VitalisLoadingScreen` | `Error → VitalisErrorScreen(onRetry)` | `Success` with **empty list** → `VitalisEmptyScreen("No active alerts")` | `Success` with data → `AlertsList` | `null → VitalisEmptyScreen`
- `AssistantScreen` adds inline loading indicator (sized `CircularProgressIndicator` in a chat bubble row) and an inline `Surface` error card for `UiState.Error`, both rendered within the `LazyColumn` chat history
- Old `ErrorText` helper composable removed — fully replaced by `VitalisErrorScreen`

## Files Involved
- [src/android/app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt](android/app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt): Activity + all Compose screen composables

## UiState Coverage

| Screen | Loading | Error | Empty | Success |
|---|---|---|---|---|
| Dashboard | `VitalisLoadingScreen` | `VitalisErrorScreen` + retry | `VitalisEmptyScreen` | `DashboardContent` |
| Alerts | `VitalisLoadingScreen` | `VitalisErrorScreen` + retry | `VitalisEmptyScreen` (no alerts) | `AlertsList` |
| Assistant | Inline spinner in chat | Inline error bubble in chat | — (chat history is naturally empty on first load) | Chat messages + citations |

## Flow (Brief)
1. `ExampleActivity.onCreate` creates ViewModels, triggers `loadDashboard` and `loadAlerts`, then calls `setContent { VitalisTheme { MainScreen(…) } }`.
2. Each tab composable observes its ViewModel's `LiveData` via `observeAsState()`.
3. A `when` expression maps every sealed class variant (including the `null` initial state) to the appropriate composable.
4. Error branches pass a retry lambda that re-triggers the ViewModel's load function with the hardcoded `userId`.

## Checklist
- [x] `VitalisTheme` applied at the root of `setContent`
- [x] Nav bar items have icons (SpaceDashboard / Notifications / Forum)
- [x] `DashboardScreen` — all 4 states handled
- [x] `AlertsScreen` — all 4 states handled, including empty-list branch
- [x] `AssistantScreen` — inline loading spinner and inline error card
- [x] `VitalisErrorScreen` retry lambdas wired to ViewModel reload functions
- [x] Old `ErrorText` composable removed

---

# Android Network Layer Expansion — Report Pipeline Endpoints

## Overview
This section documents the extension of the Android network/data layer to support four new report-pipeline endpoints from `src/backend/routes/reports.py`. All changes strictly append to the existing layer — no interceptors, error handlers, or prior endpoints were modified.

## Functionalities
- Adds `POST /reports/ocr` — runs Tesseract OCR on an already-uploaded file (`@FormUrlEncoded`)
- Adds `POST /reports/extract-labs` — extracts lab results via deterministic regex (`@FormUrlEncoded`)
- Adds `POST /reports/extract-labs-gemini` — extracts lab results via Gemini AI, idempotent (`@FormUrlEncoded`)
- Adds `POST /reports/process` — full pipeline (upload → OCR → extraction) in one call (`@Multipart`)
- Adds five new `@Serializable` response models to `Report.kt`: `OcrReportResponse`, `ExtractLabsResponse`, `GeminiExtractionLog`, `RegexExtractionResult`, `ProcessReportResponse`
- Updates `Citation` (`RagQuery.kt`) and `AlertEvidence` (`Alert.kt`) with three nullable citation fields (`sourceFilename`, `sourceUrl`, `pageNumber`) introduced by DB migration 002

## Files Involved
- [src/android/app/src/main/java/com/vitalis/health/data/model/Report.kt](android/app/src/main/java/com/vitalis/health/data/model/Report.kt): Five new response model classes added
- [src/android/app/src/main/java/com/vitalis/health/data/model/RagQuery.kt](android/app/src/main/java/com/vitalis/health/data/model/RagQuery.kt): `Citation` updated with DB migration 002 citation fields
- [src/android/app/src/main/java/com/vitalis/health/data/model/Alert.kt](android/app/src/main/java/com/vitalis/health/data/model/Alert.kt): `AlertEvidence` updated with DB migration 002 citation fields
- [src/android/app/src/main/java/com/vitalis/health/data/network/HealthApiService.kt](android/app/src/main/java/com/vitalis/health/data/network/HealthApiService.kt): Four new Retrofit endpoint declarations
- [src/android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapter.kt](android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapter.kt): Four new interface method signatures
- [src/android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapterImpl.kt](android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapterImpl.kt): Four `override` implementations using the existing `safeApiCall + unwrap` pattern
- [src/android/app/src/main/java/com/vitalis/health/data/repository/HealthRepository.kt](android/app/src/main/java/com/vitalis/health/data/repository/HealthRepository.kt): Four pass-through delegations to the adapter

## Flow (Brief)
1. A ViewModel calls a `HealthRepository` method (e.g. `processReport`).
2. The repository delegates to `HealthApiAdapterImpl`, which calls `safeApiCall { api.processReport(...).unwrap { body -> body } }`.
3. The Retrofit interface sends the request via OkHttp (passing through `VitalisInterceptor` and `HttpLoggingInterceptor` unchanged).
4. The Kotlinx Serialization converter deserialises the JSON response into the appropriate model class.
5. `ApiResult.Success` or `ApiResult.Error` is returned up to the ViewModel.

## Checklist
- [x] Five new response models added to `Report.kt`
- [x] `Citation` and `AlertEvidence` updated with DB migration 002 citation fields
- [x] All four endpoints declared across `HealthApiService`, `HealthApiAdapter`, `HealthApiAdapterImpl`, and `HealthRepository`
- [x] No interceptors, error handlers, or existing endpoints modified

---

# Report Timeline & Expanded Dashboard

## Overview

This deliverable adds a **ReportTimeline** vertical-timeline composable and expands the
Dashboard tab with a **Patient Summary**, **Wellbeing Score** card,
**Active Alerts** section, and the new timeline — all styled to match the
`sample.html` design-system tokens (colours, radii, spacing).

## Functionalities

| Feature | Description |
|---|---|
| **ReportTimeline** | Vertical timeline listing medical reports with icon, risk badge, extraction-method chip, expandable citation metadata |
| **Patient Summary** | Card showing greeting, patient ID, weather, and AQI badge |
| **Wellbeing Score** | Card with accent top bar, IBM Plex Mono score, `LinearProgressIndicator`, and trend badge |
| **Active Alerts** | Severity-coloured left-border cards with citation source filename |
| **Extraction Chip** | `AssistChip` indicating AI (Gemini) or Standard (Regex) extraction |
| **Expandable Citation** | `AnimatedVisibility` revealing source filename and page number per report |

## Files Involved

| File | Role |
|---|---|
| `android/app/src/main/java/com/vitalis/health/ui/components/ReportTimeline.kt` | New composable: `ReportTimeline`, `TimelineItemCard`, `RiskBadge`, `ExtractionChip`, `drawLeftBorder` modifier, `PLACEHOLDER_REPORTS` |
| `android/app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt` | Expanded `DashboardContent`, new private composables: `PatientSummaryCard`, `InfoChip`, `WellbeingScoreCard`, `ActiveAlertsSection`, `AlertDashboardCard` |
| `android/app/src/main/java/com/vitalis/health/ui/theme/VitalisTheme.kt` | Existing design tokens consumed (no changes) |
| `android/app/src/main/java/com/vitalis/health/data/model/Alert.kt` | `Alert` and `AlertEvidence` models consumed (no changes) |

## Design Token Mapping

These `sample.html` CSS patterns drove the Compose implementation:

| CSS class / pattern | Compose equivalent |
|---|---|
| `.timeline-item` (14dp radius, 1px border, shadow) | `TimelineItemCard` — `RoundedCornerShape(14.dp)`, `CardDefaults` elevation |
| `.timeline-icon` (38px, 10px radius) | 38.dp `Box` with `RoundedCornerShape(10.dp)` |
| `.timeline-icon.blood / .heart / .lab / .exam` | `ReportType` enum icon tints & backgrounds |
| `.risk-badge` (4dp radius, coloured bg) | `RiskBadge` — `Surface` with `RoundedCornerShape(4.dp)` |
| `.timeline-highlight` (2px left border, bg-app) | `drawLeftBorder` custom `Modifier.drawBehind` |
| `.wellness-card` (24dp radius, gradient top, 28px padding) | `WellbeingScoreCard` — `RoundedCornerShape(24.dp)`, accent `Box`, paddings |
| `.alert-card` (left border by severity) | `AlertDashboardCard` — 3dp coloured `Box` |

## Flow (Brief)

1. `ExampleActivity` creates `DashboardViewModel` via `ViewModelFactory`.
2. `DashboardScreen` observes `UiState` LiveData; on `Success` renders `DashboardContent`.
3. `DashboardContent` is a scrollable `Column` containing four sections:
   - `PatientSummaryCard` — built from `DashboardData`
   - `WellbeingScoreCard` — `MetricTextStyle` (IBM Plex Mono), progress bar, trend badge
   - `ActiveAlertsSection` — iterates `PLACEHOLDER_ALERTS`, renders `AlertDashboardCard` with severity border
   - `ReportTimeline` — iterates `PLACEHOLDER_REPORTS`, renders `TimelineItemCard` with expandable citation

---

# Deliverable 7 — Report Upload & Report Detail Screens

## Overview

Two new Compose screens plus a new ViewModel enable the full upload → OCR → extraction pipeline from the Android app. The design replicates the `sample.html` upload dropzone styling using Material 3.

## Functionalities

- **ReportUploadScreen** — Document picker (`ActivityResultContracts.GetContent`), AI/Standard extraction toggle, dropzone UI
- **ReportDetailScreen** — Displays OCR text (collapsible), confidence score, regex extraction results, Gemini extraction log
- **ReportUploadViewModel** — Drives UiState (Idle → Uploading → Processing → Success/Error), calls `repository.processReport()`
- **Timeline integration** — Newly uploaded reports are prepended to the Dashboard's `ReportTimeline`
- **Navigation** — 5th "Upload" tab in bottom navigation; success state navigates to detail view

## Files Involved

| File | Purpose |
|------|---------|
| `ui/ReportUploadViewModel.kt` | ViewModel with UiState sealed class and `uploadAndProcess()` |
| `ui/components/ReportUploadScreen.kt` | Upload dropzone, file picker, AI toggle, success screen |
| `ui/components/ReportDetailScreen.kt` | Report viewer with OCR text, extraction results |
| `ui/ViewModelFactory.kt` | Updated — registers `ReportUploadViewModel` |
| `ui/example/ExampleActivity.kt` | Updated — 5th Upload tab, wires ViewModel, timeline integration |

## Upload UiState Flow

```
Idle → (user picks file + taps Upload) → Uploading → Processing → Success / Error
                                                                        ↓
                                                              onViewResult → ReportDetailScreen
                                                              onUploadAnother → reset to Idle
```

## Backend Endpoint Used

`POST /reports/process` — the full pipeline endpoint (upload → OCR → extraction in one call).

- **Request**: multipart form — `user_id`, `file`, `use_gemini`
- **Response**: `ProcessReportResponse` with `reportId`, `storagePath`, `publicUrl`, `ocrConfidence`, `ocrTextPreview`, `regexExtraction`, `geminiExtraction`, `geminiError`

## Design Mapping (sample.html → Compose)

| sample.html | Compose |
|-------------|---------|
| `.upload-button` (dashed border, primary-light bg) | `Surface` with `BorderStroke(1.5.dp, dashed)`, `VitalisPrimaryLight` bg |
| `.upload-button svg` (18px upload icon) | `Icons.Outlined.CloudUpload` (32dp) |
| File selection indicator | `Card` with `Description` icon, filename, size, remove button |
| AI/Standard toggle | `Card` with `SmartToy` icon + `Switch` |
| Report result cards | `SectionCard`, `OcrResultCard`, `RegexExtractionCard`, `GeminiExtractionCard` |

## Checklist

- [x] `ReportUploadViewModel` — UiState sealed class (Idle/Uploading/Processing/Success/Error)
- [x] `ReportUploadScreen` — document picker via `rememberLauncherForActivityResult`
- [x] AI/Standard extraction toggle (`useGemini` boolean)
- [x] Exhaustive UiState handling using `VitalisLoadingScreen`, `VitalisErrorScreen`
- [x] `ReportDetailScreen` — collapsible OCR text, confidence bar, extraction cards
- [x] `ReportTimeline` prepends newly uploaded reports via `uploadedReports` state list
- [x] 5th "Upload" tab wired in `ExampleActivity`
- [x] `ViewModelFactory` updated with `ReportUploadViewModel`
- [x] No existing Retrofit interfaces, data models, or Repository logic modified
- [x] Build succeeds, all unit tests pass
4. Each `TimelineItemCard` is clickable — toggling `expanded` state shows citation metadata via `AnimatedVisibility`.

## Checklist

- [x] `ReportTimeline.kt` created with `ReportType`, `ExtractionMethod`, `ReportTimelineItem`, `PLACEHOLDER_REPORTS`
- [x] `TimelineItemCard` implements icon, risk badge, extraction chip, highlight with left border, expandable citation
- [x] `DashboardContent` expanded with Patient Summary, Wellbeing Score, Active Alerts, Report Timeline
- [x] All styling matches `sample.html` design tokens (colours, radii, typography)
- [x] No existing composables, models, or navigation modified — additions only
- [x] README4.md updated with documentation

---

# Profile & Consent Settings Screen

## Overview
This deliverable adds a **ProfileConsentScreen** composable — a settings/preferences screen that mirrors the profile section of `sample.html`. It includes a user profile header, data-processing toggles (including the Cloud AI / Gemini extraction flag), data-sharing consent switches, and doctor access controls. All toggle state is locally hoisted (`remember { mutableStateOf() }`) and **not** wired to a ViewModel or persistence layer.

## Functionalities

| Feature | Description |
|---|---|
| **Profile Header** | 76 dp avatar with initials, name, monospaced demographics (ID, age, gender), "Manage Account" outlined button — replicates `.profile-header-section` from HTML |
| **Data Processing Group** | "Enable Cloud AI (Gemini) Extraction" toggle with subtitle explaining AI vs regex extraction; "Auto-Extract Lab Results" static toggle |
| **Data Sharing Group** | "Share Anonymized Health Data" and "Share Usage Analytics" toggles with descriptive subtexts |
| **Doctor Access Group** | "Clinical Summary Access", "Lab Results Access", "Alert & Risk Data Access" toggles for granting/revoking provider visibility |
| **Settings Group Layout** | Grouped cards with 10 dp radius, 1 dp border, internal dividers — mirrors `.settings-group` / `.settings-item` from HTML |
| **4th Navigation Tab** | "Profile" tab added to bottom nav in `ExampleActivity` using `Icons.Outlined.Person` |

## Files Involved

| File | Changes |
|---|---|
| `android/app/src/main/java/com/vitalis/health/ui/components/ProfileConsentScreen.kt` | New composable: `ProfileConsentScreen`, `ProfileHeader`, `SettingsGroup`, `SettingsToggleItem`, `SettingsDivider` |
| `android/app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt` | 4th `NavigationBarItem` ("Profile"), `when` branch routing to `ProfileConsentScreen()`, `Person` icon import |

## Design Token Mapping

| HTML class / pattern | Compose equivalent |
|---|---|
| `.profile-avatar-large` (76px, 20px radius, primary bg) | `Box(size = 76.dp, RoundedCornerShape(20.dp), VitalisPrimary)` |
| `.profile-name` (22px, weight 700) | `Text(fontSize = 22.sp, fontWeight = Bold)` |
| `.profile-details` (13px, IBM Plex Mono) | `Text(fontSize = 13.sp, fontFamily = Monospace, letterSpacing = 0.3.sp)` |
| `.edit-profile-btn` (border 1.5px, radius-sm, bg-app) | `OutlinedButton(border = 1.5.dp, shape = 6.dp, containerColor = VitalisBgApp)` |
| `.settings-group-title` (11px, uppercase, 0.8 tracking) | `Text(fontSize = 11.sp, FontWeight.Bold, letterSpacing = 0.8.sp)` |
| `.settings-item` (14px/16px padding, white bg) | `Row(padding(horizontal = 16.dp, vertical = 14.dp))` |
| `.settings-item-icon` (30px, bg-app, 8px radius) | `Box(size = 30.dp, RoundedCornerShape(8.dp), VitalisBgApp)` |
| `.settings-item-label` (14px, weight 500) | `Text(fontSize = 14.sp, fontWeight = Medium)` |
| `.toggle-switch` (42×24, primary when on, border when off) | `Switch(checkedTrackColor = VitalisPrimary, uncheckedTrackColor = VitalisBorder)` |
| `.settings-group .settings-item` (shared border radius) | `Surface(shape = RoundedCornerShape(10.dp), border = 1.dp)` wrapping `Column` |

## Flow (Brief)
1. User taps the "Profile" bottom-nav tab in `ExampleActivity`.
2. `MainScreen` `when` block routes `selectedTab == 3` to `ProfileConsentScreen()`.
3. `ProfileConsentScreen` renders a scrollable `Column` with `ProfileHeader` + three `SettingsGroup`s.
4. Each toggle's state is local — `remember { mutableStateOf(…) }` — providing visual interactivity without ViewModel coupling.

## Checklist
- [x] `ProfileConsentScreen.kt` created with all composables
- [x] Profile header replicates HTML design (avatar, name, demographics, button)
- [x] "Enable Cloud AI (Gemini) Extraction" toggle with descriptive subtitle
- [x] Data-sharing toggles (anonymized data, usage analytics)
- [x] Doctor access toggles (summary, labs, alerts)
- [x] All styling matches `sample.html` design tokens
- [x] 4th "Profile" navigation tab added to `ExampleActivity`
- [x] Toggle state is hoisted with `remember` — no ViewModel wiring

---
---

# Backend-to-Android Integration — Real Endpoint Alignment

## Overview
This deliverable analyzes every backend endpoint against the Android network layer and updates the Android code so it works against the **real** FastAPI backend (`src/backend/main.py` and `src/backend/routes/`) wherever possible. No backend code was modified.

## Changes Made

### 1. Report Upload Path + Response Model Fix
**Problem:** `HealthApiService.uploadReport()` used path `/api/v1/reports/upload`, but both the real backend and mock server register the route at `/reports/upload`. Additionally, `ReportUploadResponse` expected `{status, report_id, message}` which matches neither backend — the real backend returns `{path, public_url}`.

**Fix:**
- `HealthApiService.kt`: Changed `@POST("/api/v1/reports/upload")` → `@POST("/reports/upload")`
- `Report.kt`: Replaced `ReportUploadResponse(status, reportId, message)` with `ReportUploadResponse(path, publicUrl)` matching the real `{path, public_url}` response

### 2. RAG Query Response Model + Adapter Fix
**Problem:** The Android `RagResponse` model expected a mock-server wrapper format `{status, data: {answer, citations}}`, but the real backend returns a flat structure `{answer, context, chunks_retrieved, grounding_available, model, llm_error}`.

**Fix:**
- `RagQuery.kt`: Rewrote `RagResponse` to match the real backend's flat format. The large `context` field is intentionally omitted (skipped by `ignoreUnknownKeys`). Added `chunksRetrieved`, `groundingAvailable`, `model`, and `llmError` fields.
- `HealthApiAdapterImpl.kt`: Updated `queryHealthAssistant()` to construct `RagData(answer = body.answer)` from the flat response instead of extracting `body.data` from a wrapper. Citations default to empty since the real backend does not return them in a flat list — they are embedded inside the deep `context` object.

### 3. Hardcoded Patient ID Fix
**Problem:** `PatientSummaryCard` in `ExampleActivity.kt` hardcoded `InfoChip(label = "Patient ID", value = "patient_001")` instead of using the data from the API.

**Fix:** Changed to `InfoChip(label = "Patient ID", value = data.userId)`.

### 4. Unit Test Update
Updated `HealthApiAdapterImplTest.queryHealthAssistant` to use the real backend response format (flat `{answer, chunks_retrieved, ...}`) instead of the mock wrapper format.

## Files Modified

| File | Change |
|---|---|
| `android/.../data/model/Report.kt` | `ReportUploadResponse` fields: `status, reportId, message` → `path, publicUrl` |
| `android/.../data/model/RagQuery.kt` | `RagResponse` rewritten from `{status, data}` wrapper to flat `{answer, chunksRetrieved, groundingAvailable, model, llmError}` |
| `android/.../data/network/HealthApiService.kt` | Upload path: `/api/v1/reports/upload` → `/reports/upload` |
| `android/.../data/adapter/HealthApiAdapterImpl.kt` | `queryHealthAssistant` constructs `RagData` from flat response |
| `android/.../ui/example/ExampleActivity.kt` | Patient ID uses `data.userId` instead of hardcoded string |
| `android/.../adapter/HealthApiAdapterImplTest.kt` | RAG test uses real backend response format |

---

## Endpoint Integration Status

### List A — Endpoints Integrated with Real Backend

| # | Method | Path | Android Method | Status |
|---|--------|------|---------------|--------|
| 1 | POST | `/reports/upload` | `uploadReport()` | **Fixed** — path corrected, response model aligned |
| 2 | POST | `/reports/ocr` | `ocrReport()` | Already aligned |
| 3 | POST | `/reports/extract-labs` | `extractLabs()` | Already aligned |
| 4 | POST | `/reports/extract-labs-gemini` | `extractLabsGemini()` | Already aligned |
| 5 | POST | `/reports/process` | `processReport()` | Already aligned |
| 6 | POST | `/api/v1/rag_query` | `queryHealthAssistant()` | **Fixed** — response model + adapter mapping aligned |

### List B — Backend Endpoints Not Used by the Android UI

| # | Method | Path | Reason |
|---|--------|------|--------|
| 1 | GET | `/health` | Infrastructure healthcheck — not relevant to user-facing UI |
| 2 | GET | `/api/v1/rag/test` | Developer/debug endpoint — returns mock retrieval context |

### List C — Android UI Features Without Real Backend Support

| # | Feature | Current Data Source | Notes |
|---|---------|-------------------|-------|
| 1 | Dashboard tab | Mock endpoint `GET /api/v1/dashboard/{user_id}` | No real backend route exists — `DashboardResponse` with `wellbeing_score`, `greeting`, `environment` is mock-only |
| 2 | Alerts tab | Mock endpoint `GET /api/v1/alerts` | No real backend route exists — `AlertsResponse` is mock-only |
| 3 | Dashboard Active Alerts section | `PLACEHOLDER_ALERTS` hardcoded list | No real alerts endpoint; dashboard shows 2 hardcoded `Alert` objects |
| 4 | Report Timeline | `PLACEHOLDER_REPORTS` hardcoded list | No backend endpoint for report history; uses 4 hardcoded `ReportTimelineItem` objects |
| 5 | Doctor Patients view | Mock endpoint `GET /api/v1/doctor/patients` | No real backend route exists — `PatientsResponse` is mock-only |
| 6 | RAG citations display | Defaults to empty list | Real backend embeds citation data in the deep `context` object rather than a flat `citations` array; extraction requires modelling `BuiltContext.rag_knowledge_base.retrieved_chunks` |
| 7 | Profile & Consent settings | Local `remember` state only | No backend endpoint for user preferences or consent flags |

---

## Architecture Preserved

The existing architecture was strictly maintained:

```
UI (Compose) → ViewModel → Repository → API Adapter → Retrofit → Backend
```

- **No interceptors modified** — `VitalisInterceptor` and `HttpLoggingInterceptor` unchanged
- **No error handling changed** — `safeApiCall`, `unwrap`, `ApiResult` pattern preserved
- **No backend code modified** — all changes are Android-side only
- **`ignoreUnknownKeys = true`** in Kotlinx Serialization config ensures forward compatibility with new backend fields

## Checklist

- [x] Report upload path corrected (`/api/v1/reports/upload` → `/reports/upload`)
- [x] `ReportUploadResponse` model aligned with real backend `{path, public_url}`
- [x] `RagResponse` model aligned with real backend flat format
- [x] RAG adapter mapping updated (no more `body.data` wrapper extraction)
- [x] Hardcoded `"patient_001"` replaced with `data.userId` in PatientSummaryCard
- [x] Unit test updated to use real backend response format
- [x] Three endpoint lists (A, B, C) documented
- [x] No backend code modified
- [x] No interceptors, logging, or error handling modified

---

# Dashboard Refactoring — Environment, Location & Dynamic Reports

## Overview
This deliverable refactors the Android dashboard to fetch real data from backend endpoints, integrate GPS location services for environment data (AQI/weather), and replace hardcoded placeholder reports with dynamic data.

## API Contract Changes

### GET /api/v1/environment
Fetches real-time AQI and weather data for the user's location.

**Request:**
```
GET /api/v1/environment?user_id={userId}&latitude={lat}&longitude={lon}&city={cityName}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | UUID of the user |
| latitude | float | Yes | GPS latitude (-90 to 90) |
| longitude | float | Yes | GPS longitude (-180 to 180) |
| city | string | No | Optional city name |

**Response (200 OK):**
```json
{
  "location_city": "Mumbai",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "temperature_celsius": 32.5,
  "humidity_percent": 65.0,
  "aqi_level": 85,
  "weather_condition": "Partly Cloudy",
  "fetched_at": "2024-03-21T10:30:00Z"
}
```

### GET /reports/user/{user_id}
Fetches paginated report history for the dashboard timeline.

**Request:**
```
GET /reports/user/{user_id}?limit=20&offset=0
```

**Response (200 OK):**
```json
{
  "user_id": "...",
  "count": 5,
  "total": 12,
  "reports": [
    {
      "report_id": "...",
      "report_name": "Blood Test",
      "upload_date": "2024-03-15T08:00:00Z",
      "report_type": "blood",
      "risk_label": "Normal",
      "risk_level": "normal",
      "processing_status": "completed",
      "lab_results_count": 8
    }
  ]
}
```

## State Management Updates

### DashboardViewModel
- Changed from `LiveData` to `StateFlow`
- Concurrent network calls using `async/await`
- Added `LocationData` class for GPS coordinates

```kotlin
sealed class UiState {
    data object Loading : UiState()
    data class Success(data: DashboardData, locationAvailable: Boolean) : UiState()
    data class Error(message: String) : UiState()
    data class LocationPermissionRequired(data: DashboardData?) : UiState()
}
```

## Location Services Integration

**Permissions added to AndroidManifest.xml:**
```xml
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

**Dependency:**
```kotlin
implementation("com.google.android.gms:play-services-location:21.1.0")
```

**Flow:** App requests location → FusedLocationProviderClient → coordinates sent to /api/v1/environment → AQI/weather displayed

## Dynamic Reports
- Removed `PLACEHOLDER_REPORTS` hardcoded data
- `ReportSummary.toTimelineItem()` converts backend data to UI model
- Report types mapped: blood → BLOOD, cardiac → HEART, exam → EXAM, others → LAB

---

# Alerts Integration — End-to-End

## Overview
Full integration of the Android alerts system with the backend deterministic rules engine.

## API Contract

### GET /alerts/{user_id}
Fetches all alerts for a user with evidence linking back to source reports.

**Request:**
```
GET /alerts/{user_id}?include_evidence=true
```

**Response (200 OK):**
```json
{
  "user_id": "...",
  "count": 3,
  "alerts": [
    {
      "id": "uuid",
      "severity": "high",
      "reason": "High LDL detected (180 mg/dL) exceeds threshold of 160",
      "created_at": "2024-03-21T10:00:00Z",
      "evidence": [
        {
          "id": "uuid",
          "report_id": "uuid",
          "lab_result_id": "uuid",
          "ocr_text_snippet": "LDL 180 mg/dL"
        }
      ]
    }
  ]
}
```

### POST /alerts/evaluate/{user_id}
Runs the rules engine and persists new alerts (idempotent).

**Response:**
```json
{
  "user_id": "...",
  "alerts_triggered": 3,
  "deleted": 2,
  "inserted": 3,
  "evidence_inserted": 5
}
```

## Rules Engine (13 Deterministic Rules)

| # | Rule ID | Description | Severity |
|---|---------|-------------|----------|
| 1 | any_abnormal | Any lab result with abnormal_flag=true | medium |
| 2 | low_hemoglobin | Hemoglobin < 12 g/dL | high |
| 3 | high_cholesterol | Total cholesterol ≥ 200 | medium |
| 4 | high_ldl | LDL ≥ 160 | medium |
| 5 | high_blood_sugar | Fasting glucose ≥ 100 | high |
| 6 | high_hba1c | HbA1c ≥ 5.7% | high |
| 7 | abnormal_tsh | TSH < 0.4 or > 4.5 | medium |
| 8 | low_vitamin_d | Vitamin D < 30 ng/mL | low |
| 9 | low_b12 | B12 < 300 pg/mL | low |
| 10 | high_creatinine | Creatinine ≥ 1.3 | medium |
| 11 | low_platelets | Platelets < 150 ×10³/µL | high |
| 12 | abnormal_wbc | WBC < 2 or > 11 ×10³/µL | high |
| 13 | missing_critical | No CBC or metabolic panel found | low |

## Android Data Models

**Alert.kt:**
```kotlin
@Serializable
data class Alert(
    val id: String,
    val severity: String,  // "high" | "medium" | "low"
    val reason: String,
    @SerialName("created_at") val createdAt: String,
    val evidence: List<AlertEvidence> = emptyList()
)

@Serializable
data class AlertEvidence(
    val id: String?,
    @SerialName("report_id") val reportId: String?,
    @SerialName("lab_result_id") val labResultId: String?,
    @SerialName("ocr_text_snippet") val ocrTextSnippet: String?
)

@Serializable
data class AlertsApiResponse(
    @SerialName("user_id") val userId: String,
    val count: Int,
    val alerts: List<Alert>
)
```

## AlertsViewModel (StateFlow)

```kotlin
class AlertsViewModel(private val repository: HealthRepository) : ViewModel() {
    sealed class UiState {
        data object Loading : UiState()
        data class Success(val alerts: List<Alert>) : UiState()
        data class Error(val message: String) : UiState()
    }

    private val _alertsState = MutableStateFlow<UiState>(UiState.Loading)
    val alertsState: StateFlow<UiState> = _alertsState.asStateFlow()

    fun loadAlerts(userId: String) { /* fetches from repository */ }
    fun retry() { /* reloads with cached userId */ }
}
```

## Data Flow

```
Backend Rules Engine → alerts table → GET /alerts/{user_id}
                                            ↓
Android: HealthApiService → HealthApiAdapterImpl → HealthRepository
                                            ↓
         AlertsViewModel (StateFlow) → AlertsScreen (Compose)
```

## Files Modified

| File | Change |
|------|--------|
| `AlertsViewModel.kt` | LiveData → StateFlow, added retry() |
| `ExampleActivity.kt` | observeAsState() → collectAsState() |
| `ExampleActivity.kt` | Fixed ReportType mapping (removed IMAGING/SPECIALIST) |

## Checklist

- [x] Alert models aligned with backend JSON schema
- [x] AlertsViewModel uses StateFlow for consistency
- [x] Alerts sorted by severity (high → medium → low) in repository
- [x] Evidence data included for explainability
- [x] Build errors fixed (ReportType enum values)
- [x] Documentation complete

---

# Authentication Flow Implementation

## Overview
Complete authentication system for the Vitalis Health Android app, including login and registration flows connected to the backend API. Implements secure token management with automatic auth header injection.

## Functionalities
- User login with email/password
- User registration with full name, email, and password
- JWT token persistence using SharedPreferences
- Automatic Authorization header injection for authenticated requests
- Form validation (email format, password strength, password confirmation)
- Error handling with user-friendly messages
- Loading states with progress indicators

## Backend API Endpoints

### POST /auth/login
Authenticate user with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "user_id": "uuid-string",
  "access_token": "jwt-token",
  "refresh_token": "jwt-token"
}
```

### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "role": "patient"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user_id": "uuid-string",
  "access_token": "jwt-token",
  "refresh_token": "jwt-token"
}
```

## Android Data Models

**AuthModels.kt:**
```kotlin
@Serializable
data class UserLoginRequest(
    @SerialName("email") val email: String,
    @SerialName("password") val password: String
)

@Serializable
data class UserRegisterRequest(
    @SerialName("email") val email: String,
    @SerialName("password") val password: String,
    @SerialName("full_name") val fullName: String,
    @SerialName("role") val role: String = "patient"
)

@Serializable
data class AuthResponse(
    @SerialName("message") val message: String,
    @SerialName("user_id") val userId: String,
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String
)
```

## Token Management

**TokenManager.kt:**
```kotlin
class TokenManager(context: Context) {
    var accessToken: String?
    var refreshToken: String?
    var userId: String?
    val isLoggedIn: Boolean

    fun saveAuthData(accessToken: String, refreshToken: String, userId: String)
    fun clearAuthData()
}
```

- Uses SharedPreferences for persistence
- Automatically injected into VitalisInterceptor for auth headers
- Stored in VitalisApp singleton for app-wide access

## AuthViewModel (StateFlow)

```kotlin
class AuthViewModel(
    private val repository: HealthRepository,
    private val tokenManager: TokenManager
) : ViewModel() {
    sealed class AuthUiState {
        data object Idle : AuthUiState()
        data object Loading : AuthUiState()
        data class Success(val authResponse: AuthResponse) : AuthUiState()
        data class Error(val message: String) : AuthUiState()
    }

    val authState: StateFlow<AuthUiState>
    val email: StateFlow<String>
    val password: StateFlow<String>
    val fullName: StateFlow<String>

    fun login()
    fun register()
    fun logout()
    fun isLoggedIn(): Boolean
}
```

## UI Components

**LoginScreen.kt:**
- Email and password input fields with VitalisTheme styling
- Show/hide password toggle
- Form validation (email format, required fields)
- Loading state with spinner in button
- Error snackbar with VitalisDanger color
- Navigation to RegisterScreen

**RegisterScreen.kt:**
- Full name, email, password, and confirm password fields
- Password strength validation (min 6 characters)
- Password confirmation matching
- Show/hide toggles for both password fields
- Loading state with spinner
- Error snackbar
- Navigation to LoginScreen

## Data Flow

```
User Input → AuthViewModel → HealthRepository → HealthApiAdapter
                    ↓
            TokenManager.saveAuthData()
                    ↓
VitalisInterceptor (auto-adds "Bearer <token>" header)
                    ↓
          All subsequent API calls
```

## Automatic Authorization Header

**VitalisInterceptor.kt:**
```kotlin
override fun intercept(chain: Interceptor.Chain): Response {
    var request = chain.request()
    val isAuthEndpoint = url.contains("/auth/login") || url.contains("/auth/register")

    if (!isAuthEndpoint) {
        tokenManager?.accessToken?.let { token ->
            request = request.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        }
    }
    // ... proceed with request
}
```

## Files Created

| File | Description |
|------|-------------|
| `data/model/AuthModels.kt` | Login/Register request and AuthResponse models |
| `data/local/TokenManager.kt` | Token persistence using SharedPreferences |
| `ui/AuthViewModel.kt` | Authentication ViewModel with StateFlow |
| `ui/components/LoginScreen.kt` | Login UI with Jetpack Compose |
| `ui/components/RegisterScreen.kt` | Registration UI with Jetpack Compose |

## Files Modified

| File | Change |
|------|--------|
| `data/network/HealthApiService.kt` | Added login() and register() endpoints |
| `data/adapter/HealthApiAdapter.kt` | Added auth method signatures |
| `data/adapter/HealthApiAdapterImpl.kt` | Implemented auth methods with safeApiCall |
| `data/repository/HealthRepository.kt` | Added login() and register() functions |
| `di/NetworkModule.kt` | Accept TokenManager for auth header injection |
| `di/VitalisInterceptor.kt` | Auto-inject Authorization Bearer token |
| `ui/ViewModelFactory.kt` | Added AuthViewModel with TokenManager |
| `VitalisApp.kt` | Initialize TokenManager in DI graph |

## UI Styling

All components use VitalisTheme design tokens:
- **Background**: `MaterialTheme.colorScheme.background` (VitalisBgApp)
- **Input Fields**: `surfaceVariant` (VitalisBgInput) with `shapes.medium` (14.dp rounded)
- **Buttons**: `primary` (VitalisPrimary) with white text
- **Typography**: `headlineLarge` for titles, `bodyMedium` for labels
- **Errors**: `VitalisDanger` color for error text and snackbars
- **Borders**: `VitalisPrimary` on focus, transparent when unfocused

## Usage Example

```kotlin
// In Activity:
val app = application as VitalisApp
val authViewModel = ViewModelProvider(this, app.viewModelFactory)[AuthViewModel::class.java]

// Check logged in status:
if (authViewModel.isLoggedIn()) {
    val userId = authViewModel.getUserId()
    navigateToDashboard(userId)
}

// In Compose:
LoginScreen(
    viewModel = authViewModel,
    onLoginSuccess = { userId ->
        navController.navigate("dashboard/$userId")
    },
    onNavigateToRegister = {
        navController.navigate("register")
    }
)
```

## Validation Rules

| Field | Validation |
|-------|----------|
| Email | Must match Android email pattern |
| Password (Login) | Required, non-empty |
| Password (Register) | Minimum 6 characters |
| Confirm Password | Must match password field |
| Full Name | Required, non-empty |

## Checklist

- [x] Auth data models created (UserLoginRequest, UserRegisterRequest, AuthResponse)
- [x] Backend API endpoints added to HealthApiService
- [x] HealthApiAdapter and HealthRepository updated
- [x] TokenManager implemented with SharedPreferences
- [x] Automatic Authorization header injection via VitalisInterceptor
- [x] AuthViewModel with StateFlow for UI state management
- [x] ViewModelFactory updated to support AuthViewModel
- [x] LoginScreen composable with form validation
- [x] RegisterScreen composable with password confirmation
- [x] VitalisTheme styling applied consistently
- [x] Error handling with snackbars
- [x] Loading states with progress indicators
- [x] Documentation complete

---

# Environment Feature Implementation (AQI & Weather)

## Overview

Implemented a comprehensive environment monitoring feature that displays Air Quality Index (AQI) and weather data based on the user's current location. The feature integrates location services, backend API calls, and a polished UI component following VitalisTheme design standards.

## Architecture Components

### 1. Location Tracking Infrastructure

Created an abstraction layer for location services to enable testability and clean architecture:

**LocationTracker Interface:**
```kotlin
interface LocationTracker {
    suspend fun getCurrentLocation(): Location?
}
```

**DefaultLocationTracker Implementation:**
- Uses Google Play Services `FusedLocationProviderClient`
- Checks for location permissions (`ACCESS_COARSE_LOCATION`, `ACCESS_FINE_LOCATION`)
- Verifies GPS/Network providers are enabled
- Fast path: attempts `getLastKnownLocation()` first
- Falls back to `requestCurrentLocation()` with fresh location request
- Uses `suspendCancellableCoroutine` for async operations
- Handles SecurityException and permission revocation gracefully

```kotlin
class DefaultLocationTracker(
    private val locationClient: FusedLocationProviderClient,
    private val application: Application
) : LocationTracker {
    override suspend fun getCurrentLocation(): Location?
}
```

### 2. Data Models

The `EnvironmentData` model (in `Dashboard.kt`) represents the backend `/api/v1/environment` response:

```kotlin
@Serializable
data class EnvironmentData(
    @SerialName("location_city") val locationCity: String?,
    val latitude: Double?,
    val longitude: Double?,
    @SerialName("temperature_celsius") val temperatureCelsius: Double?,
    @SerialName("humidity_percent") val humidityPercent: Double?,
    @SerialName("aqi_level") val aqiLevel: Int?,
    @SerialName("weather_condition") val weatherCondition: String?,
    @SerialName("fetched_at") val fetchedAt: String?
)
```

### 3. UI Component: EnvironmentCard

**Features:**
- **AQI Display:** Color-coded severity levels based on EPA Air Quality Index standards
  - Good (0-50): Green (`VitalisSuccess`)
  - Moderate (51-100): Blue (`VitalisPrimary`)
  - Unhealthy for Sensitive (101-150): Orange (`VitalisWarning`)
  - Unhealthy (151-200): Orange (`VitalisWarning`)
  - Very Unhealthy (201-300): Red (`VitalisDanger`)
  - Hazardous (301+): Red (`VitalisDanger`)

- **Weather Metrics Row:**
  - Temperature (°C) with thermometer icon
  - Humidity (%) with water drop icon
  - Weather condition with cloud icon

- **Location Badge:** Displays city name with location pin icon

- **Loading State:** Centered spinner during data fetch

- **Permission Prompt:** Displays when location permission is not granted
  - Icon, message, and "Enable Location" button
  - Callback to request permissions from parent Activity/Fragment

**Component Signature:**
```kotlin
@Composable
fun EnvironmentCard(
    environmentData: EnvironmentData?,
    isLoading: Boolean = false,
    locationAvailable: Boolean = true,
    onRequestPermission: (() -> Unit)? = null,
    modifier: Modifier = Modifier
)
```

### 4. Styling and Design

All components follow VitalisTheme design tokens:
- **Card Surface:** `MaterialTheme.colorScheme.surface` with 2.dp elevation
- **AQI Section:** Rounded 12.dp surface with alpha-blended color backgrounds
- **Location Badge:** 6.dp rounded, `VitalisBgInput` background
- **Weather Metrics:** Icon + value + label vertical layout
- **Typography:** Material 3 typography scale (`titleMedium`, `bodySmall`, `headlineMedium`)
- **Colors:** Semantic colors for AQI severity, muted text for secondary info

### 5. Dependency Injection

Updated `VitalisApp` to initialize `LocationTracker` in the DI graph:

```kotlin
class VitalisApp : Application() {
    lateinit var locationTracker: LocationTracker
        private set

    override fun onCreate() {
        super.onCreate()
        // ...
        val fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)
        locationTracker = DefaultLocationTracker(fusedLocationClient, this)
    }
}
```

## Usage Example

### In a Composable Screen:

```kotlin
// Request location permission launcher
val locationPermissionLauncher = rememberLauncherForActivityResult(
    contract = ActivityResultContracts.RequestMultiplePermissions()
) { permissions ->
    val fineGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] ?: false
    val coarseGranted = permissions[Manifest.permission.ACCESS_COARSE_LOCATION] ?: false
    if (fineGranted || coarseGranted) {
        // Re-fetch environment data
        viewModel.refreshEnvironment()
    }
}

// Display the card
EnvironmentCard(
    environmentData = dashboardState.environment,
    isLoading = environmentLoading,
    locationAvailable = locationAvailable,
    onRequestPermission = {
        locationPermissionLauncher.launch(
            arrayOf(
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION
            )
        )
    }
)
```

### In ViewModel:

```kotlin
suspend fun fetchEnvironmentData() {
    val location = (application as VitalisApp).locationTracker.getCurrentLocation()
    location?.let {
        val result = repository.getEnvironment(it.latitude, it.longitude)
        // Handle result
    }
}
```

## Files Created

| File | Description |
|------|-------------|
| `location/LocationTracker.kt` | Interface for location services abstraction |
| `location/DefaultLocationTracker.kt` | Implementation using FusedLocationProviderClient |
| `ui/components/EnvironmentCard.kt` | Composable for displaying AQI and weather data |

## Files Modified

| File | Change |
|------|--------|
| `VitalisApp.kt` | Initialize `LocationTracker` in DI graph |
| `data/model/Dashboard.kt` | Already contained `EnvironmentData` model |

## Prerequisites (Already in Place)

- **Manifest Permissions:** `ACCESS_COARSE_LOCATION`, `ACCESS_FINE_LOCATION`
- **Dependencies:** `play-services-location` in `build.gradle.kts`
- **Backend API:** `/api/v1/environment` endpoint accepting lat/lon query params

## AQI Standards Reference

Based on EPA Air Quality Index:

| AQI Range | Level | Description | Action |
|-----------|-------|-------------|--------|
| 0-50 | Good | Air quality is satisfactory | None needed |
| 51-100 | Moderate | Acceptable quality for most | Unusually sensitive people should consider limiting prolonged outdoor exertion |
| 101-150 | Unhealthy for Sensitive | Sensitive groups may be affected | Active children and adults, and people with respiratory disease should limit prolonged outdoor exertion |
| 151-200 | Unhealthy | Everyone may experience effects | Active children and adults, and people with respiratory disease should avoid prolonged outdoor exertion |
| 201-300 | Very Unhealthy | Health alert: serious effects | Everyone should avoid all outdoor exertion |
| 301+ | Hazardous | Health emergency conditions | Everyone should remain indoors |

## Error Handling

The implementation gracefully handles:
- Missing location permissions → Shows permission prompt
- Disabled location services → Returns null from tracker
- Permission revoked during request → Catches SecurityException
- Missing environment data → Shows empty state
- Backend API errors → Handled by repository layer's `ApiResult` sealed class

## Testing Considerations

The `LocationTracker` abstraction allows for:
- **Unit testing ViewModels:** Mock the interface to return test locations
- **UI testing:** Inject a fake implementation without GPS hardware
- **Integration testing:** Use real FusedLocationProviderClient with test locations

## Checklist

- [x] LocationTracker interface created for abstraction
- [x] DefaultLocationTracker implementation with FusedLocationProviderClient
- [x] Permission checking (COARSE + FINE location)
- [x] Location service availability checks (GPS + Network)
- [x] Last known location fast path
- [x] Fresh location request with suspendCancellableCoroutine
- [x] EnvironmentCard composable with VitalisTheme styling
- [x] AQI color-coded display with EPA standards
- [x] Weather metrics row (temperature, humidity, condition)
- [x] Location badge with city name
- [x] Loading state UI
- [x] Permission prompt UI with callback
- [x] LocationTracker added to VitalisApp DI graph
- [x] Documentation complete

---

# Authentication Flow Integration — Dynamic Navigation & Logout

## Overview

Refactored the app entry point (`ExampleActivity`) to implement proper authentication state management, removing hard-coded user IDs and enabling dynamic login/logout navigation. Added logout functionality to the Profile screen.

## Changes Made

### 1. AppState Navigation Enum

Created a simple state machine for app navigation:

```kotlin
enum class AppState {
    LOGIN,
    REGISTER,
    MAIN
}
```

### 2. ExampleActivity Refactoring

**Before:** Hard-coded `userId = "4ba33076-3a1c-42b7-93c9-0096b3cfe88a"` and immediately rendered `MainScreen`.

**After:**
- Instantiates `AuthViewModel` alongside other ViewModels
- Checks `authVm.isLoggedIn()` on launch to determine initial state
- Uses `when (appState)` to render the appropriate screen:
  - `LOGIN` → `LoginScreen` with navigation callbacks
  - `REGISTER` → `RegisterScreen` with navigation callbacks
  - `MAIN` → Retrieves `userId` dynamically via `authVm.getUserId()`

**Navigation Callbacks:**
```kotlin
LoginScreen(
    viewModel = authVm,
    onLoginSuccess = { userId ->
        alertsVm.loadAlerts(userId)
        appState = AppState.MAIN
    },
    onNavigateToRegister = { appState = AppState.REGISTER }
)

RegisterScreen(
    viewModel = authVm,
    onRegisterSuccess = { userId ->
        alertsVm.loadAlerts(userId)
        appState = AppState.MAIN
    },
    onNavigateToLogin = { appState = AppState.LOGIN }
)
```

**Logout Implementation:**
```kotlin
MainScreen(
    ...
    onLogoutClick = {
        authVm.logout()
        appState = AppState.LOGIN
    }
)
```

### 3. MainScreen Signature Update

Added `onLogoutClick` callback parameter:

```kotlin
@Composable
fun MainScreen(
    ...
    onLogoutClick: () -> Unit = {}
)
```

Passes the callback to `ProfileConsentScreen`:
```kotlin
4 -> ProfileConsentScreen(onLogoutClick = onLogoutClick)
```

### 4. ProfileConsentScreen Update

Added `onLogoutClick` parameter and "Log Out" button:

```kotlin
@Composable
fun ProfileConsentScreen(
    onLogoutClick: () -> Unit = {}
)
```

**Logout Button Styling:**
- Uses `VitalisDanger` for border and text color
- Transparent container to indicate destructive action
- Positioned below "Manage Account" button
- Consistent styling with VitalisTheme design tokens

```kotlin
OutlinedButton(
    onClick = onLogoutClick,
    shape = RoundedCornerShape(6.dp),
    border = BorderStroke(1.5.dp, VitalisDanger),
    colors = ButtonDefaults.outlinedButtonColors(
        containerColor = Color.Transparent,
        contentColor = VitalisDanger,
    ),
    ...
) {
    Text("Log Out", ...)
}
```

## Data Flow

```
App Launch
    ↓
authVm.isLoggedIn()?
    ├── true  → AppState.MAIN → MainScreen(userId from TokenManager)
    └── false → AppState.LOGIN → LoginScreen
                                      ↓
                              onLoginSuccess(userId)
                                      ↓
                              AppState.MAIN → MainScreen
                                      ↓
                              Profile Tab → ProfileConsentScreen
                                      ↓
                              "Log Out" button clicked
                                      ↓
                              authVm.logout() + AppState.LOGIN
```

## Files Modified

| File | Change |
|------|--------|
| `ui/example/ExampleActivity.kt` | Added `AppState` enum, `AuthViewModel` instantiation, state-based navigation, `onLogoutClick` callback |
| `ui/components/ProfileConsentScreen.kt` | Added `onLogoutClick` parameter and "Log Out" button styled with `VitalisDanger` |

## Security Considerations

- `TokenManager.clearAuthData()` is called on logout (via `AuthViewModel.logout()`)
- Access token, refresh token, and user ID are all cleared from SharedPreferences
- App state resets to `LOGIN`, preventing access to authenticated screens

## Checklist

- [x] Removed hard-coded `userId` from ExampleActivity
- [x] Added `AppState` enum for navigation state management
- [x] Instantiated `AuthViewModel` in ExampleActivity
- [x] Initial state determined by `authVm.isLoggedIn()`
- [x] LOGIN state renders `LoginScreen` with callbacks
- [x] REGISTER state renders `RegisterScreen` with callbacks
- [x] MAIN state retrieves `userId` dynamically from `authVm.getUserId()`
- [x] Null `userId` redirects to LOGIN state
- [x] `MainScreen` accepts `onLogoutClick` callback
- [x] `ProfileConsentScreen` accepts `onLogoutClick` callback
- [x] "Log Out" button added with `VitalisDanger` styling
- [x] Logout calls `authVm.logout()` and resets to LOGIN state
- [x] Documentation complete

---

# Wearable Vitals Pipeline Integration

## Overview

Complete end-to-end implementation of wearable device vitals synchronization from Health Connect to backend. Enables users to sync heart rate, steps, sleep, SpO2, HRV, calories, and active minutes from fitness trackers and smartwatches.

## Context

Healthcare apps benefit from continuous health monitoring through wearable devices. Android Health Connect provides unified access to health data from various wearable manufacturers (Fitbit, Samsung, Garmin, etc.). This feature creates a seamless pipeline: Device → Health Connect → Vitalis App → Backend → AI Analysis.

## Implementation

### 1. Dependencies & Permissions

**build.gradle.kts:**
```kotlin
implementation("androidx.health.connect:connect-client:1.1.0-alpha07")
```

**AndroidManifest.xml:**
- 8 Health Connect read permissions (heart rate, steps, sleep, SpO2, HRV, calories)
- Privacy policy activity for permission rationale (required by Health Connect)
- Package query for Health Connect app detection

**res/values/health_permissions.xml:**
- Array resource for Play Store health permissions compliance

### 2. Data Layer

**data/model/Vitals.kt** (NEW):
- `VitalReading`: Core model with `recorded_at`, `metric_type`, `value`, `unit`, `device_id`
- `IngestVitalsRequest/Response`: Batch upload with `inserted` and `skipped` counts
- `VitalsSummaryResponse`: 7-day aggregated metrics (`min`, `max`, `avg`, `latest`)
- `WearableContext`: Device metadata for multi-device tracking

**data/network/HealthApiService.kt:**
```kotlin
POST /api/v1/ingest/vitals          // Batch upload readings
GET  /api/v1/vitals/{user_id}/summary        // 7-day aggregates
GET  /api/v1/vitals/{user_id}/readings       // Detailed time-series
```

**data/repository/HealthRepository.kt:**
- Added `ingestVitals()`, `getVitalsSummary()`, `getVitalsReadings()` methods
- Uses existing `ApiResult` wrapper for error handling

### 3. Health Connect Integration

**healthconnect/HealthConnectManager.kt** (NEW):
- Checks availability: `Available`, `NotInstalled`, `NotSupported`
- Manages 8 Health Connect permissions
- Reads all metric types with time range support
- Converts Health Connect records to `VitalReading` models
- Returns `HealthConnectReadResult` with readings and error messages

**Key methods:**
```kotlin
checkAvailability(): HealthConnectAvailability
hasAllPermissions(): Boolean
createPermissionRequestContract(): ActivityResultContract
readVitals(startTime, endTime, deviceId): HealthConnectReadResult
readVitalsForDays(days): HealthConnectReadResult
```

### 4. ViewModel Layer

**ui/VitalsViewModel.kt** (NEW):
- **State Management**: `HealthConnectState`, `PermissionState`, `SyncState`, `SummaryState`
- **Sync Flow**: Read from Health Connect → Transform to API format → Upload to backend
- **Summary Loading**: Fetch 7-day aggregated metrics from backend
- **Convenience Getters**: `getTodaySteps()`, `getAverageHeartRate()`, `getTotalSleepHours()`, etc.

**ui/VitalsViewModelFactory.kt** (NEW):
- Factory for creating `VitalsViewModel` with `HealthConnectManager` dependency

### 5. UI Layer

**ui/components/VitalsDashboardScreen.kt** (NEW - ~870 lines):

**Flow:**
```
Availability Check → Permission Request → Sync Button → Metrics Display
```

**Key Composables:**
- `VitalsDashboardScreen`: Root with state observation
- `PermissionRequestScreen`: Permission rationale and request flow
- `HealthConnectUnavailableScreen`: Not installed / not supported states
- `LoadedVitalsDashboardContent`: Main dashboard with sync and metrics
- `SyncButton`: Upload with Reading/Uploading/Success/Error states
- `KeyMetricsRow`: 3 prominent metrics (steps, heart rate, sleep)
- `MetricDetailCard`: Expandable cards with 7-day trends (min/max/avg)

**Metric Types Displayed:**
- Steps, Heart Rate, Sleep Minutes, SpO2, Resting Heart Rate, HRV, Calories, Active Minutes

**ui/PrivacyPolicyActivity.kt** (NEW):
- Required by Health Connect for permission rationale
- Displays Vitalis privacy policy covering data collection, usage, storage, sharing, and user rights

### 6. Navigation Integration

**ui/example/ExampleActivity.kt:**
- Instantiated `VitalsViewModel` with `VitalsViewModelFactory`
- Added "Vitals" tab (position 1) with `MonitorHeart` icon
- Tab routing: Dashboard(0), **Vitals(1)**, Upload(2), Alerts(3), Chat(4), Profile(5)

```kotlin
val healthConnectManager = HealthConnectManager(this)
val vitalsFactory = VitalsViewModelFactory(app.repository, healthConnectManager)
vitalsVm = ViewModelProvider(this, vitalsFactory)[VitalsViewModel::class.java]

NavigationBarItem(
    selected = selectedTab == 1,
    onClick = { selectedTab = 1 },
    label = { Text("Vitals") },
    icon = { Icon(Icons.Outlined.MonitorHeart, contentDescription = "Vitals") }
)
```

## Data Flow

```
Wearable Device (Fitbit/Samsung/Garmin)
    ↓
Health Connect (System App)
    ↓
HealthConnectManager.readVitalsForDays(7)
    ↓
Transform to List<VitalReading>
    ↓
HealthRepository.ingestVitals(userId, readings)
    ↓
Backend /api/v1/ingest/vitals
    ↓
Success: Refresh Summary
    ↓
HealthRepository.getVitalsSummary(userId, 7)
    ↓
Backend /api/v1/vitals/{user_id}/summary
    ↓
Display 7-day Aggregates (min/max/avg/latest)
```

## Files Created

| File | Purpose |
|------|---------|
| `healthconnect/HealthConnectManager.kt` | Health Connect API integration, permission handling, data reading |
| `ui/VitalsViewModel.kt` | State management, sync orchestration, summary loading |
| `ui/VitalsViewModelFactory.kt` | ViewModel factory with HealthConnectManager dependency |
| `ui/components/VitalsDashboardScreen.kt` | Complete Compose UI for vitals dashboard |
| `ui/PrivacyPolicyActivity.kt` | Privacy policy screen (Health Connect requirement) |
| `data/model/Vitals.kt` | Data models for vitals API (VitalReading, Ingest, Summary) |
| `res/values/health_permissions.xml` | Play Store health permissions compliance |

## Files Modified

| File | Change |
|------|--------|
| `build.gradle.kts` | Added Health Connect client dependency |
| `AndroidManifest.xml` | Added 8 health permissions, privacy policy activity, Health Connect query |
| `data/network/HealthApiService.kt` | Added 3 vitals endpoints (ingest, summary, readings) |
| `data/adapter/HealthApiAdapter.kt` | Added vitals method signatures |
| `data/adapter/HealthApiAdapterImpl.kt` | Implemented vitals API calls |
| `data/repository/HealthRepository.kt` | Added `ingestVitals()`, `getVitalsSummary()`, `getVitalsReadings()` |
| `ui/example/ExampleActivity.kt` | Instantiated VitalsViewModel, added Vitals navigation tab |

## Edge Cases Handled

- **Health Connect Not Installed**: Show install prompt with Play Store intent
- **Device Not Supported**: Show "Not Available" message for incompatible devices
- **Permissions Denied**: Show permission rationale and request button
- **No Data Available**: Show empty state with "Sync Now" prompt
- **Sync Errors**: Display error message with retry option
- **Network Failures**: ApiResult error handling with user-friendly messages

## Security & Privacy

- All health permissions explicitly declared in manifest
- Privacy policy accessible before permission grant
- Data encrypted in transit (HTTPS)
- No data stored locally (fetched from backend on demand)
- User can revoke permissions anytime via system settings

## Checklist

- [x] Health Connect dependency added to build.gradle
- [x] 8 health permissions added to AndroidManifest
- [x] Privacy policy activity created and registered
- [x] Data models created matching backend API contract
- [x] 3 vitals endpoints added to network layer
- [x] HealthConnectManager implemented with availability check
- [x] VitalsViewModel created with sync and summary logic
- [x] Comprehensive UI built with Jetpack Compose
- [x] Permission flow implemented (check → request → grant)
- [x] Sync flow implemented (read → transform → upload)
- [x] Integrated into main navigation with Vitals tab
- [x] Error handling for all edge cases
- [x] Documentation complete

---

# Environment Data Integration & User Management

## Overview
Enhanced the Android client with location-aware RAG queries and comprehensive user profile management capabilities.

## Features Implemented

### 1. Location-Aware RAG Queries
**Objective:** Pass user location data to RAG endpoint for context-aware health recommendations (weather, AQI integration).

**Implementation:**
- **AssistantViewModel.kt**: Integrated `LocationTracker` to automatically fetch GPS coordinates before each RAG query
- **HealthRepository.kt**: Extended `queryAssistant()` to accept optional location parameters (`userLat`, `userLon`, `userLocation`)
- **HealthApiAdapter.kt**: Updated `queryHealthAssistant()` signature to pass location context to backend
- **ViewModelFactory.kt**: Added `LocationTracker` dependency injection for `AssistantViewModel`

**Result:** RAG queries now automatically include user location when available, enabling AI to provide weather and air quality-aware health advice. Gracefully handles missing permissions.

### 2. User Management CRUD Operations
**Objective:** Implement update, delete, and fetch-by-email operations for user profiles.

**Backend Endpoints Added:**
- `PATCH /api/v1/users/{user_id}` - Update user profile
- `DELETE /api/v1/users/{user_id}` - Delete account (cascade delete)
- `GET /api/v1/users/email/{email}` - Fetch user by email

**Data Models:**
- **User.kt**: Created `UserUpdateRequest` with optional fields (fullName, phone, dateOfBirth, gender, location, health metrics)

**Network Layer:**
- **HealthApiService.kt**: Added 3 new Retrofit endpoints
- **HealthApiAdapterImpl.kt**: Implemented adapter methods with proper error handling
- **HealthRepository.kt**: Added repository methods (`updateUser`, `deleteUser`, `getUserByEmail`)

**ViewModel:**
- **AuthViewModel.kt**: Added `ProfileUiState` sealed class and methods:
  - `updateUserProfile()` - Updates profile via PATCH
  - `deleteUser()` - Deletes account and clears tokens via `TokenManager`
  - `getUserByEmail()` - Fetches user by email

### 3. Profile Management UI
**Objective:** Provide user-friendly screens for profile editing and account deletion.

**ProfileEditScreen.kt:**
- Material 3 Compose UI with organized sections (Personal Info, Location, Health Metrics)
- Pre-populated form fields from current user profile
- Real-time validation and loading states
- Success/error handling with Snackbar notifications
- Fields: Name, Phone, DOB, Gender, City, State, Country, Blood Group, Height, Weight

**SettingsScreen.kt:**
- Card-based layout with three main actions:
  - Edit Profile (navigate to ProfileEditScreen)
  - Logout (clears session and returns to login)
  - Delete Account (Danger Zone with confirmation dialog)
- **Delete Confirmation Dialog:**
  - Lists all data to be deleted (profile, reports, vitals, alerts)
  - Clear warning: "This action cannot be undone"
  - Automatic token clearing and navigation on success

## Files Created

| File | Purpose |
|------|---------|
| `ui/components/ProfileEditScreen.kt` | Compose UI for editing user profile with form validation |
| `ui/components/SettingsScreen.kt` | Settings screen with logout and account deletion |
| `ui/components/ProfileNavigationIntegration.kt` | Documentation and integration examples for navigation |

## Files Modified

| File | Change |
|------|--------|
| `data/model/User.kt` | Added `UserUpdateRequest` data class |
| `data/network/HealthApiService.kt` | Added PATCH, DELETE, GET endpoints for user management |
| `data/adapter/HealthApiAdapter.kt` | Added method signatures for user CRUD operations |
| `data/adapter/HealthApiAdapterImpl.kt` | Implemented user management + location-aware RAG calls |
| `data/repository/HealthRepository.kt` | Added user management + location parameters to RAG |
| `ui/AssistantViewModel.kt` | Integrated `LocationTracker` for automatic location fetching |
| `ui/AuthViewModel.kt` | Added profile management methods and `ProfileUiState` |
| `ui/ViewModelFactory.kt` | Added `LocationTracker` dependency injection |
| `VitalisApp.kt` | Updated factory instantiation with `locationTracker` |

## Architecture Highlights

- **Clean Architecture**: All layers follow MVVM pattern (Model → Repository → ViewModel → UI)
- **Kotlin Coroutines**: Async operations with proper error handling via `ApiResult` wrapper
- **StateFlow**: Reactive state management for UI updates
- **Graceful Degradation**: Location unavailable → falls back to null (RAG still works)
- **Security**: Account deletion automatically clears all tokens via `TokenManager`

## Data Flow: Profile Update

```
User edits form → "Save Changes" button
    ↓
ProfileEditScreen validates input
    ↓
viewModel.updateUserProfile(userId, updateRequest)
    ↓
AuthViewModel → ProfileUiState.Loading
    ↓
HealthRepository.updateUser(userId, request)
    ↓
PATCH /api/v1/users/{user_id}
    ↓
Success: ProfileUiState.Success → Snackbar → Navigate back
Error: ProfileUiState.Error → Show error message
```

## Data Flow: Account Deletion

```
Settings → "Delete My Account" button
    ↓
DeleteAccountDialog shows warning + data list
    ↓
User confirms → viewModel.deleteUser(userId)
    ↓
DELETE /api/v1/users/{user_id}
    ↓
Success: tokenManager.clearAuthData() → Navigate to Login
Error: Show error, user remains logged in
```

## Checklist

- [x] Location tracking integrated into RAG queries
- [x] User update endpoint implemented (PATCH)
- [x] User delete endpoint implemented (DELETE)
- [x] Get user by email endpoint implemented (GET)
- [x] UserUpdateRequest data model created
- [x] ProfileUiState added to AuthViewModel
- [x] ProfileEditScreen UI created with Material 3
- [x] SettingsScreen UI created with deletion dialog
- [x] Token clearing on account deletion
- [x] Graceful location permission handling
- [x] Error handling across all layers
- [x] Documentation complete

---

# Secure Report PDF Delivery (Signed URL + Native PDF Renderer)

## Overview

Implemented an end-to-end secure report viewing flow for private Supabase storage objects using short-lived signed URLs.

The backend now issues a temporary download link only to the report owner, and Android now:

- requests the signed URL from backend
- downloads the PDF into app-internal cache (`context.cacheDir`)
- renders pages natively with `PdfRenderer`
- shares the cached PDF via `FileProvider` with `Intent.ACTION_SEND`

This avoids proxying large PDF payloads through FastAPI while preserving authorization and privacy controls.

## Backend Changes

### New Endpoint

- **GET** `/reports/{report_id}/download_url`

### Behavior

- Verifies auth via `get_current_user`.
- Enforces ownership using `WHERE id = report_id AND user_id = current_user`.
- Reads `storage_path` from `medical_reports`.
- Generates a **60-second** Supabase signed URL from private reports bucket.
- Returns:

```json
{
    "signed_url": "https://..."
}
```

### Resilience/Compatibility

- Added fallback for older rows/schemas without `storage_path` by deriving path from `source_url`.
- Normalizes signed URL payloads across supabase-py response shapes (`signed_url`, `signedUrl`, `signedURL`, nested `data`).

### Files Updated (Backend)

- `backend/routes/reports.py`
- `backend/controllers/reports_controller.py` (stores `storage_path` in pending report row when schema supports it)

## Android Data Layer Changes

### API Contract

- Added:

```kotlin
@GET("/reports/{report_id}/download_url")
suspend fun getReportDownloadUrl(@Path("report_id") reportId: String): Response<ReportDownloadUrlResponse>
```

### New Model

- `ReportDownloadUrlResponse(signedUrl: String)` mapped from `signed_url`.

### Adapter + Repository

- Added `fetchReportDownloadUrl(reportId: String): ApiResult<String>` in adapter.
- Added `getReportDownloadUrl(reportId: String): ApiResult<String>` in repository.

### Files Updated (Android Data)

- `android/app/src/main/java/com/vitalis/health/data/model/Report.kt`
- `android/app/src/main/java/com/vitalis/health/data/network/HealthApiService.kt`
- `android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapter.kt`
- `android/app/src/main/java/com/vitalis/health/data/adapter/HealthApiAdapterImpl.kt`
- `android/app/src/main/java/com/vitalis/health/data/repository/HealthRepository.kt`

## Android ViewModel + UI Rendering

### New ViewModel

- `ReportDetailViewModel`
    - Fetches signed URL from repository.
    - Downloads PDF to `cacheDir` via `HttpURLConnection`.
    - Validates PDF readability and page count via `PdfRenderer`.
    - Exposes `PdfState` (`Idle`, `Loading`, `Ready`, `Error`).

### Native PDF Rendering

- Added `PdfRendererViewer` composable wrapper around Android native `PdfRenderer`.
- Displays a vertically scrollable list of pages rendered into bitmaps.
- Performs rendering off the main thread.

### Report Detail UX

- `ReportDetailScreen` now:
    - loads secure PDF automatically for selected `reportId`
    - shows loading while URL fetch + cache download occurs
    - renders PDF pages once ready
    - exposes share action in top app bar

### Share/Export

- Added secure share flow using:
    - `Intent.ACTION_SEND`
    - `FileProvider` URI grant (`FLAG_GRANT_READ_URI_PERMISSION`)

### Files Updated (Android UI)

- `android/app/src/main/java/com/vitalis/health/ui/ReportDetailViewModel.kt` (new)
- `android/app/src/main/java/com/vitalis/health/ui/components/PdfRendererViewer.kt` (new)
- `android/app/src/main/java/com/vitalis/health/ui/components/ReportDetailScreen.kt` (rewritten)
- `android/app/src/main/java/com/vitalis/health/ui/ViewModelFactory.kt`
- `android/app/src/main/java/com/vitalis/health/ui/example/ExampleActivity.kt`
- `android/app/src/main/java/com/vitalis/health/ui/components/ReportUploadScreen.kt` (button text updated to "View Report")

## Android Manifest / FileProvider

Added FileProvider so cached internal files can be shared safely without exposing filesystem paths.

### Files Updated

- `android/app/src/main/AndroidManifest.xml`
- `android/app/src/main/res/xml/file_paths.xml` (new)

## Security Notes

- Signed URLs are short-lived (60s).
- Ownership check enforced server-side before URL issuance.
- PDFs are downloaded to internal app cache only.
- No writes to external/public downloads.
- Sharing uses temporary URI permissions through `FileProvider`.

## Validation

- Android compile check passed:
    - `./gradlew :app:compileDebugKotlin --no-daemon`
