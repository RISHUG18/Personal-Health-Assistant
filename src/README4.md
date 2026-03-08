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

Ask the AI Coach a question and receive an answer with citations.

| Response Code | Description |
|---------------|-------------|
| 200 | AI answer with source citations |

### 4. Report Upload Endpoint
**POST** `/api/v1/reports/upload`

Upload a medical PDF for processing (multipart/form-data).

| Response Code | Description |
|---------------|-------------|
| 202 | Accepted for processing with report_id |

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
| status | string | "success" or "error" |
| data.answer | string | AI-generated response |
| data.citations | array | List of source citations (source_file, page, snippet) |

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
Calls **POST** `/api/v1/rag_query` with a JSON body and returns the AI answer with citations.

### 4. Upload Report
```kotlin
suspend fun uploadReport(userId: String, fileName: String, fileBytes: ByteArray): ApiResult<ReportUploadResponse>
```
Calls **POST** `/api/v1/reports/upload` as multipart/form-data.

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
