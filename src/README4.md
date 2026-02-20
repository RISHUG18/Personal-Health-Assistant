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
