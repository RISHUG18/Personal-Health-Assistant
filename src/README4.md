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
