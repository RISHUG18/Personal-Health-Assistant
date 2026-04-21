# `src/` — Source Code Directory

This directory contains all source code for the **Personal Health Assistant** monorepo — a full-stack AI health platform with a Python/FastAPI backend, a browser-based frontend, an Android app, and a Supabase database layer.

---

## Top-Level Structure

```
src/
├── android/          # Android mobile application (Kotlin)
├── backend/          # Python FastAPI server — the core AI pipeline
├── db/               # Database schema & migrations (Supabase/PostgreSQL)
├── frontend/         # Vanilla HTML/JS doctor-dashboard web interface
├── mock-data/        # Seed scripts and test fixtures
├── sample_reports/   # Sample medical PDF reports for testing
└── types/            # Shared TypeScript type definitions (api.ts)
```

---

## `android/` — Android Mobile Application

Kotlin-based Android app that serves as the patient-facing mobile interface.

```
android/
├── ARCHITECTURE.md              # Design overview of the Android app
├── build.gradle.kts             # Root Gradle build configuration
├── settings.gradle.kts          # Gradle project settings (module declarations)
├── gradle.properties            # JVM / Gradle performance settings
├── gradlew / gradlew.bat        # Gradle wrapper scripts (Unix / Windows)
├── build_output.txt             # Last captured build output log
└── app/
    ├── build.gradle.kts         # App-module Gradle config (dependencies, SDK versions, etc.)
    └── src/
        ├── main/
        │   ├── AndroidManifest.xml   # App permissions, activities, services declaration
        │   ├── java/                 # Kotlin/Java source files (activities, viewmodels, etc.)
        │   └── res/                  # Android resources (layouts, drawables, strings, etc.)
        └── test/                     # Unit tests for Android-layer logic
```

---

## `backend/` — Python FastAPI Server

The heart of the system. A **FastAPI** application that orchestrates document ingestion, AI query answering (RAG pipeline), health alert generation, and wearable data aggregation.

```
backend/
├── main.py               # Application entrypoint — registers all routers and middleware
├── requirements.txt      # Python package dependencies
├── .env                  # Local environment variables (Supabase keys, Gemini API key)
├── .gitignore
├── __init__.py
│
├── config/               # Infrastructure clients
├── contracts/            # API specification and context schema
├── controllers/          # Business logic handlers (called by routes)
├── extraction/           # Gemini-powered medical PDF data extraction pipeline
├── labs/                 # Lab-test normalisation dictionary and engine
├── middleware/           # JWT authentication middleware
├── models/               # Shared Pydantic data models
├── ocr/                  # OCR text pre-processing utilities
├── prompts/              # LLM system prompt and citation instruction text files
├── routes/               # FastAPI route definitions (HTTP layer)
├── rules/                # Deterministic health alert rules engine
├── scripts/              # Offline utilities, cron jobs, and seed scripts
├── services/             # Core service sub-packages (embeddings, retrieval, LLM, etc.)
└── tests/                # Test suite (unit, integration, smoke)
```

### `backend/main.py`
The FastAPI application entry point. Loads `.env`, configures CORS to allow frontend and local origins, and mounts every route module. Also registers a `/health` endpoint and a legacy `/voice_chat` backward-compatibility alias.

---

### `backend/config/`

| File | Purpose |
|---|---|
| `supabase_client.py` | Singleton factory for the Supabase Python client. Reads `SUPABASE_URL` and `SUPABASE_KEY` from environment. All DB-accessing modules import `get_supabase_client()` from here. |
| `__init__.py` | Package marker. |

---

### `backend/contracts/`

Formal interface definitions for cross-team contract agreement.

| File | Purpose |
|---|---|
| `api_spec.yaml` | OpenAPI-style specification for all public API endpoints. |
| `context_schema.json` | JSON Schema describing the `BuiltContext` object that is assembled by the context builder and sent to Gemini. Defines size constraints (max 10 chunks, 500 chars/chunk, 4000 total chars). |

---

### `backend/controllers/`

Business logic layer that sits between routes and the database. Routes are thin; controllers contain the actual query/mutation logic.

| File | Purpose |
|---|---|
| `doctor_controller.py` | Doctor-dashboard operations: list assigned patients, fetch patient summaries, reports, and alerts for a doctor's panel. |
| `reports_controller.py` | Medical report management: listing, fetching, deleting, and status-checking of uploaded reports. |
| `users_controller.py` | User profile operations: reading and updating user demographics (name, DOB, gender, weight, height). |
| `__init__.py` | Package marker. |

---

### `backend/extraction/`

End-to-end pipeline that converts raw OCR text from a medical PDF into structured `lab_results` rows in Supabase.

| File | Purpose |
|---|---|
| `pipeline.py` | **Orchestrator.** `process_report_with_gemini(report_id)` runs the 5-step pipeline: (1) Fetch OCR text → (2) Send to Gemini → (3) Log extracted items → (4) Insert into `lab_results` → (5) Update report metadata. |
| `gemini_extractor.py` | Calls the Google Gemini API with the OCR text and a structured extraction prompt. Returns a parsed `GeminiExtractionResult` with a list of `LabResult` objects. |
| `inserter.py` | Idempotent DB writer. Deletes old `lab_results` rows for the given `report_id`, then inserts freshly extracted rows. Returns `(inserted, skipped, skip_reasons)`. |
| `normalizer.py` | Post-extraction normalization: standardises units (e.g. `"mmol/L"` vs `"mM"`), coerces text values to numeric when safe, and strips noise from reference ranges. |
| `models.py` | Pydantic models for the extraction layer: `LabResult`, `ExtractionMetadata`, `GeminiExtractionResult`, `ExtractionLogEntry`. |
| `__init__.py` | Package marker; re-exports `process_report_with_gemini`. |

---

### `backend/labs/`

Lab-test name normalisation system that maps arbitrary OCR-extracted test names to a canonical dictionary.

| File | Purpose |
|---|---|
| `normalization.py` | Core normalisation logic. Loads `lab_test_dictionary.json`, builds multi-level lookup indexes (exact canonical match → alias match → compact whitespace-stripped match → fuzzy match via `rapidfuzz`). Exports `normalize_test_name()`, `normalize_lab_name()`, `get_catalog()`, `seed_reference_tables()`, and `add_aliases_by_code()`. |
| `__init__.py` | Package marker; re-exports `normalize_lab_name`. |

**Key JSON asset (referenced at runtime):**
- `../rules/lab_test_dictionary.json` — master dictionary of ~100+ canonical lab tests with codes, aliases, units, and categories.

---

### `backend/middleware/`

| File | Purpose |
|---|---|
| `auth_middleware.py` | FastAPI dependency functions: `get_current_user()` (verifies Supabase JWT, returns `user_id`), `get_current_user_with_role()` (also returns role for RBAC), and `verify_service_role()` (validates the `SUPABASE_SERVICE_ROLE_KEY` for cron/admin endpoints). |
| `__init__.py` | Package marker. |

---

### `backend/models/`

| File | Purpose |
|---|---|
| `user.py` | `UserProfile` Pydantic model for API request/response validation. Includes demographic fields (name, DOB, gender, weight, height). |
| `__init__.py` | Package marker. |

---

### `backend/ocr/`

Thin abstraction layer for OCR pre-processing, designed so the OCR engine can be swapped without changing upstream callers.

| File | Purpose |
|---|---|
| `ocr_engine.py` | Defines the `OCREngine` abstract base class / protocol. |
| `extractors.py` | Concrete extractors that read text from uploaded PDFs (currently wraps the extraction pipeline). |
| `normalizers.py` | Normalizes raw OCR output (whitespace, encoding artefacts). |
| `inserters.py` | Inserts OCR text into `medical_reports.ocr_text`. |
| `preprocessor.py` | Pre-processing steps applied before extraction (e.g. deskew hints, noise cleanup). |
| `pipeline.py` | Thin orchestrator that wires the above together. |
| `README.md` | Design notes for the OCR subsystem. |
| `__init__.py` | Package marker with public re-exports. |

---

### `backend/prompts/`

Plain-text files loaded at runtime by `services/llm/prompt_builder.py`. Each file is a self-contained system or citation prompt.

| File | Purpose |
|---|---|
| `system_user.txt` | Behavioural rules for the **patient-facing** wellbeing coach persona (tone, scope, safety guardrails). |
| `system_doctor.txt` | Behavioural rules for the **doctor-facing** clinical assistant persona (more technical, evidence-based). |
| `system_summarizer_user.txt` | System prompt used when generating weekly health summaries for patients. |
| `system_summarizer_doctor.txt` | System prompt used when generating weekly health summaries for doctors. |
| `citation_user.txt` | Grounding / citation instructions appended to the user-turn when the patient role is active. |
| `citation_doctor.txt` | Grounding / citation instructions for the doctor role. |
| `citation_summarizer.txt` | Citation instructions for the weekly summariser role. |
| `data_extraction.txt` | Prompt used by `gemini_extractor.py` to instruct Gemini on how to extract structured lab data from OCR text. |

---

### `backend/routes/`

FastAPI `APIRouter` modules — the HTTP layer. Each file maps URL paths to async handler functions; heavy logic is delegated to controllers or services.

| File | Prefix | Description |
|---|---|---|
| `rag.py` | `POST /api/v1/rag_query` | **Primary AI pipeline.** Retrieval → data fetching → context assembly → Gemini generation. Returns `{answer, context, chunks_retrieved, model, llm_error}`. |
| `reports.py` | `/reports`, `/api/v1/reports` | Upload new PDFs, list reports, fetch individual report details, delete reports, trigger re-extraction. |
| `alerts.py` | `/alerts` | Fetch stored alerts (`GET /{user_id}`); run the rules engine (`POST /evaluate/{user_id}`); admin sweep (`POST /admin/evaluate/{user_id}` — service-role only). |
| `auth.py` | `/auth` | Register new users (`POST /register`); log in (`POST /login`); token refresh. |
| `users.py` | `/users` | Read and update the authenticated user's profile. |
| `upload.py` | `/upload` | Protected structured-upload endpoint that accepts a PDF, OCRs it, and triggers extraction. |
| `vitals.py` | `/vitals` | Ingest wearable data (`POST /vitals`); retrieve the 7-day vitals summary (`GET /vitals/{user_id}/summary`). |
| `environment.py` | `/environment` | Fetch live AQI + weather data from Open-Meteo for a given city or coordinates; cache to DB. |
| `voice.py` | `/voice`, `/voice_chat` | Handle text/voice input, run through the RAG pipeline, and return an audio or text response. |
| `summaries.py` | `/summaries` | Generate a new AI weekly health summary (`POST /summaries/generate`); retrieve stored summaries (`GET /summaries/{user_id}`). |
| `doctor.py` | `/doctor` | Doctor dashboard: patient list, per-patient summaries, reports, and alerts for all assigned patients. |
| `report_status_ws.py` | `/ws/report-status` | WebSocket endpoint that sends real-time processing status updates as a PDF is being processed. |
| `debug.py` | `/debug` | Internal diagnostics routes (safe to call in dev; not exposed in production docs). |
| `__init__.py` | — | Package marker. |

---

### `backend/rules/`

A **deterministic, configuration-driven** health alert rules engine. No ML — all thresholds are defined in JSON.

| File | Purpose |
|---|---|
| `config.json` | JSON configuration of all rule thresholds (e.g. HbA1c > 6.5 → high severity, SpO2 < 90 → critical). Controls wearable, lab, sleep, and cardio rule groups. |
| `definitions.py` | Implements all individual rules as Python functions. Each rule receives a user's lab results / wearable summary and returns an `AlertRecord`. Currently covers 13+ conditions including diabetes markers, lipid abnormalities, anemia, thyroid dysfunction, renal impairment, and wearable-derived alerts (low steps, poor sleep, abnormal HR). |
| `engine.py` | `evaluate_rules(client, user_id, ...)` — loads lab data and wearable summary, runs all rules from `definitions.py`, and returns a list of triggered `AlertRecord` objects. |
| `inserter.py` | `persist_alerts(client, user_id, alerts)` — idempotent write: deletes existing alerts for the user, inserts new ones, and links `alert_evidence` rows referencing the triggering lab result IDs. |
| `environment.py` | Environmental rules: evaluates AQI-based alerts (e.g. high pollution → asthma risk warning). |
| `lab_test_dictionary.json` | Canonical dictionary of ~100+ lab tests used for normalization. Each entry has `code`, `canonical_name`, `aliases`, `units`, `category`, and `reference_range`. |
| `models.py` | `AlertRecord` and `Severity` enum used by the rules engine. |
| `README.md` | Documents rules categories, configuration format, and extension guide. |
| `__init__.py` | Package marker. |

---

### `backend/scripts/`

Standalone executable utilities — cron jobs, seed scripts, and developer tools.

| File | Purpose |
|---|---|
| `cron_nightly_alerts.py` | **Nightly cron job.** Fetches all active patients from Supabase, fans out concurrent `POST /alerts/admin/evaluate/{user_id}` calls (bounded by `asyncio.Semaphore(10)`), and logs a summary. Exits non-zero on any failure so schedulers can alert. |
| `cron_weekly_summarizer.py` | **Weekly cron job.** Generates AI weekly health summaries for all active patients by calling `POST /summaries/generate`. Uses the same concurrency pattern. |
| `seed_users.py` | Inserts synthetic demo patient and doctor accounts with realistic profile data into Supabase for development/demo. |
| `demo_personas.py` | Creates fully fleshed-out demo personas (lab results, wearable data, reports) for specific test scenarios. |
| `ingest_supabase_reports.py` | Bulk-ingests medical PDF reports from a local directory into Supabase (OCR + extraction). |
| `create_test_user.py` | Creates a single test user via the Supabase auth API. |
| `impersonate.py` | Generates a Supabase JWT for a user to facilitate manual API testing without a frontend. |
| `mock_server.py` | Lightweight mock HTTP server returning static fixtures; used for frontend development without a live backend. |
| `eval_retrieval.py` | Evaluates retrieval quality by running a set of test queries against the pgvector index and reporting chunk count and timing. |
| `migrate_lab_results_normalization.py` | One-off migration: re-normalizes all existing `lab_results.test_name` values using the current dictionary. |
| `remap_unmapped_tests.py` | Attempts to re-match `unmapped_tests` rows to canonical codes after the dictionary has been updated. |
| `test_voice.py` | Manual end-to-end test for the voice/audio pipeline. |
| `__init__.py` | Package marker. |
| `data/` | Data directory used by scripts (e.g. local fixtures, export CSVs). |

---

### `backend/services/`

Core service sub-packages, each responsible for a discrete technical domain.

```
services/
├── __init__.py
├── context/             # Context assembly: builds the BuiltContext object sent to Gemini
├── embeddings/          # Query embedding via SentenceTransformer
├── environment/         # Open-Meteo AQI/weather fetching and caching
├── llm/                 # Gemini API client and prompt construction
├── preprocessing/       # Text cleaning and chunking for RAG indexing
├── retrieval/           # Vector search (pgvector + FAISS fallback) and indexing
├── summaries/           # AI weekly health summary generation
├── wearable/            # Wearable vitals ingestion, aggregation, and summary
│
├── privacy.py           # PII redaction utilities for prompt sanitisation
├── reports_repository.py # Data-access methods for the medical_reports table
├── reports_service.py   # Thin service layer over reports_repository
├── report_status_ws.py  # WebSocket state management for report processing status
└── mock_retrieval.py    # Returns static mock chunks (for UI tests, no DB needed)
```

#### `services/context/`

Responsible for assembling all retrieved data into a validated `BuiltContext` object.

| File | Purpose |
|---|---|
| `context_builder.py` | Pure function `build_context(...)`. Takes fetched dicts (chunks, alerts, lab snapshot, wearable data, environment, trended labs, user profile) and returns a fully validated `BuiltContext` Pydantic model. Enforces size caps: max 10 chunks, 500 chars/chunk, 4000 chars total. Also defines all Pydantic sub-models: `UserProfile`, `MedicalSnapshot`, `WearableData`, `AlertItem`, `EnvironmentalContext`, `RagKnowledgeBase`, `BuiltContext`. |
| `data_fetchers.py` | Thin DB adapter functions. Each function queries one Supabase table and returns a plain dict for `build_context` to consume. Functions: `fetch_active_alerts`, `fetch_user_lab_snapshot`, `fetch_user_profile`, `fetch_cached_environment`, `fetch_wearable_vitals`, `fetch_wearable_gap_filled_arrays` (async, calls `get_daily_wearable_aggregates` RPC), `fetch_trended_labs` (async, calls `get_trended_labs` RPC). All errors are caught and return empty fallbacks. |
| `__init__.py` | Re-exports `build_context`. |

#### `services/embeddings/`

| File | Purpose |
|---|---|
| `sentence_transformer_embedder.py` | Wraps `sentence-transformers` to encode text into dense vectors. Used by the FAISS retrieval path and the indexer to embed report chunks. |
| `query_embedding.py` | `embed_query(text)` — convenience function that returns a float vector for a single query string. Used by both pgvector and FAISS retrieval. |
| `interfaces.py` | Abstract base `Embedder` protocol. |
| `__init__.py` | Package marker. |

#### `services/environment/`

| File | Purpose |
|---|---|
| `service.py` | `EnvironmentService.get_snapshot_for_coordinates(user_id, lat, lon)` — fetches live AQI (Open-Meteo Air Quality API) and weather data, persists to the `environmental_data` table, and returns an `EnvironmentalSnapshot`. |
| `store.py` | DB read/write helpers for the `environmental_data` table. |
| `models.py` | `EnvironmentalSnapshot` Pydantic model. `to_context_dict()` converts it to the shape expected by `build_context`. |
| `interfaces.py` | Abstract `EnvironmentStore` protocol. |
| `fetchers.py` | HTTP calls to Open-Meteo endpoints (air quality, current weather). |
| `__init__.py` | Re-exports `get_environment_service()` factory. |

#### `services/llm/`

| File | Purpose |
|---|---|
| `gemini_service.py` | `GeminiService.generate(query, context_dict, system_instruction)` — calls the Google Gemini API with the assembled context and system prompt, returning the generated markdown answer string. |
| `prompt_builder.py` | `build_prompt(context_dict, query, role)` — serialises the `BuiltContext` dict into the formatted user-turn text sent to Gemini. Also provides `load_system_prompt(role)` and `load_citation_instructions(role)` which read and cache the corresponding files from `backend/prompts/`. |
| `interfaces.py` | `LLMProvider` abstract protocol. |
| `__init__.py` | Re-exports `GeminiService`, `LLMProvider`, `build_prompt`, `load_system_prompt`, `load_citation_instructions`. |

#### `services/preprocessing/`

| File | Purpose |
|---|---|
| `text_cleaning.py` | Regex-based text cleaning: removes OCR artefacts, normalises whitespace, strips control characters. |
| `gemini_cleaning.py` | Gemini-assisted cleaning pass for OCR text that has severe formatting corruption (table misalignment, merged words). |
| `chunking.py` | Splits cleaned OCR text into overlapping chunks suitable for embedding. Respects paragraph boundaries and configurable max chunk size. |
| `__init__.py` | Package marker. |

#### `services/retrieval/`

| File | Purpose |
|---|---|
| `__init__.py` | **Unified entry point.** `retrieve_context(user_id, query, strategy)` dispatches to pgvector (default) with automatic FAISS fallback. If both fail, returns an empty list (graceful degradation). Also exports `index_report`, `reindex_report`, `find_stale_reports`. |
| `pgvector_retrieval.py` | `retrieve_pgvector(...)` — calls the `match_report_chunks` Supabase RPC (HNSW cosine similarity search). Supports optional `section_filter` for targeted retrieval. |
| `faiss_retrieval.py` | `retrieve_faiss(...)` and `FaissRetriever` class — fetches all embeddings for a user from Supabase into memory and runs a local FAISS index search. Used as the offline/fallback path. |
| `indexer.py` | `index_report(report_id)` — cleans, chunks, embeds, and upserts an OCR report's chunks into the `report_chunks` table. Also provides `reindex_report` (forced re-index) and `find_stale_reports` (detects chunks whose source report has been updated). |
| `mock_retrieval.py` | Returns static hardcoded mock chunks for UI smoke tests that don't need a live DB. |

#### `services/summaries/`

| File | Purpose |
|---|---|
| `generator.py` | `generate_weekly_summary(user_id, role)` — fetches recent labs, alerts, and wearable data, assembles a context, and calls Gemini with the summariser system prompt to produce a narrative weekly health summary. |
| `__init__.py` | Re-exports `generate_weekly_summary`. |

#### `services/wearable/`

| File | Purpose |
|---|---|
| `service.py` | `WearableService.get_vitals_summary(user_id, days)` — queries the `wearable_vitals` table, computes per-metric aggregates (avg, min, max, latest, sample count), and returns a `VitalsSummary`. Also provides `get_raw_readings(user_id, metric_type, days)` for streak analysis. |
| `store.py` | DB-level read helpers for the `wearable_vitals` table, including a batch insert path. |
| `models.py` | `VitalMetric`, `VitalsSummary` Pydantic models. `VitalsSummary.to_context_dict()` converts to the flat dict that `build_context` expects. |
| `interfaces.py` | Abstract `WearableStore` protocol. |
| `__init__.py` | Re-exports `get_wearable_service()` singleton factory. |

---

### `backend/tests/`

| File / Folder | Purpose |
|---|---|
| `alerts_test.py` | Unit tests for the deterministic rules engine — tests each of the 13 rules in isolation with synthetic lab data. |
| `cleaning_pipeline_test.py` | Unit tests for text cleaning and chunking logic. |
| `test_retrieval.py` | Integration tests for both pgvector and FAISS retrieval paths. |
| `test_full_pipeline.py` | End-to-end integration test: upload PDF → OCR → extract → retrieve → RAG query. |
| `test_auth.py` | Unit tests for JWT middleware and auth endpoints. |
| `test_auth_e2e.py` | End-to-end tests for register/login/token flows. |
| `test_upload.py` | Tests for the file upload and report ingestion endpoint. |
| `test_lab_normalization.py` | Unit tests for `normalize_test_name` covering exact, alias, compact, and fuzzy match paths. |
| `test_dictionary_alias_updates.py` | Tests for `add_aliases_by_code` and collision detection. |
| `test_env_rules.py` | Tests for environmental alert rule evaluation. |
| `test_text_cleaning.py` | Tests for OCR text normalisation functions. |
| `embedding_smoke_test.py` | Smoke test: verifies the embedder returns a plausible vector. |
| `rag_cleaning_smoke_test.py` | Smoke test: verifies the Gemini cleaning pass doesn't crash. |
| `rag_cleaning_supabase_test.py` | Integration smoke test using a live Supabase connection. |
| `fixtures/` | JSON/text fixtures used across the test suite (synthetic lab results, mock OCR text). |
| `__init__.py` | Package marker. |

---

## `db/` — Database Schema & Migrations

PostgreSQL schema managed via numbered SQL migrations applied to Supabase.

```
db/
├── schema.sql       # Canonical base schema (tables, indexes, comments)
├── schema.md        # Human-readable schema documentation
└── migrations/      # Ordered SQL migration files
```

### `db/schema.sql`
Defines the initial table set:
- `medical_reports` — uploaded PDF metadata + OCR text
- `lab_results` — structured extracted lab values
- `tests_master`, `test_aliases`, `test_units` — lab normalisation reference tables
- `unmapped_tests` — extraction failures awaiting manual review
- `alerts` + `alert_evidence` — generated health alerts with provenance links

### `db/migrations/`

Each file is applied in numeric order. File names self-document intent:

| Migration | What it does |
|---|---|
| `000_create_users_table.sql` | Users table with auth fields, role, demographics |
| `001_add_report_chunks.sql` | `report_chunks` table + `match_report_chunks` pgvector RPC for vector similarity search |
| `002_add_report_chunk_metadata.sql` | Adds metadata JSONB column to `report_chunks` |
| `003_add_chunk_section_metadata.sql` | Adds `section_label` for targeted retrieval filtering |
| `004_add_processing_status.sql` | `processing_status` column on `medical_reports` |
| `005_add_section_filter_to_rpc.sql` | Extends `match_report_chunks` RPC with optional section filter |
| `006_add_environmental_data.sql` | `environmental_data` table for AQI/weather cache |
| `007_add_env_evidence_to_alert_evidence.sql` | Adds `environmental_evidence` JSONB to `alert_evidence` |
| `008_add_wearable_vitals.sql` | `wearable_vitals` table for time-series device data |
| `009_auth_and_reports.sql` | Row-level security policies for auth on reports |
| `010_vitals_cleanup_job.sql` | Scheduled cleanup job for stale vitals data |
| `011_add_health_summaries.sql` | `health_summaries` table for AI-generated weekly summaries |
| `012_add_text_value_to_lab_results.sql` | Adds `text_value` column (for non-numeric lab values) |
| `013_add_age_to_users.sql` | Adds `age` column (later dropped) |
| `014_drop_age_column.sql` | Drops `age`; age is now calculated from `date_of_birth` at query time |
| `015_privacy_hardening.sql` | Comprehensive RLS policies for data isolation between users |
| `016_lab_test_normalization.sql` | Adds `normalization_confidence` to `lab_results`; creates `tests_master`, `test_aliases`, `test_units` |
| `017_ensure_env_evidence_column.sql` | Safe idempotent addition of `environmental_evidence` column |
| `018_add_get_trended_labs_rpc.sql` | `get_trended_labs` PostgreSQL RPC — returns the 3 most recent readings per canonical lab test (window function) |
| `019_add_get_daily_wearable_aggregates_rpc.sql` | `get_daily_wearable_aggregates` RPC — returns gap-aware per-day wearable metric aggregates for LLM context |
| `020_fix_get_vitals_summary_window_and_trends.sql` | Fixes the vitals summary window function for edge cases |
| `021_fix_trend_points_count.sql` | Corrects the trend data point count in the trended labs RPC |
| `022_fix_vitals_summary_timezone_and_hr_types.sql` | Timezone-aware aggregation and HR type coercion fixes |
| `023_fix_daily_aggregation_max_per_day.sql` | Ensures at most one aggregate row per day per metric (deduplication fix) |

---

## `frontend/` — Doctor Dashboard Web Interface

Vanilla HTML + JavaScript single-page-style web interface, primarily for the doctor-facing dashboard.

```
frontend/
├── doctor-login.html      # Login page for doctors
├── doctor-dashboard.html  # Main dashboard: patient list, summary cards, alert overview
├── doctor-patient.html    # Per-patient detail view: reports, lab results, alerts, AI query panel
├── doctor-admin.html      # Admin panel for system management tasks
└── js/
    ├── api.js             # Shared HTTP client helpers for backend API calls (patient-facing)
    ├── doctor-api.js      # HTTP client helpers specific to the doctor dashboard API
    ├── components.js      # Reusable UI component rendering functions (tables, cards, modals)
    └── demo-data.js       # Static demo data for frontend development without a live backend
```

---

## `mock-data/` — Seed Data & Test Fixtures

Reference data and generator scripts for populating a development Supabase instance.

| File | Purpose |
|---|---|
| `generate_test_pdfs.js` | Node.js script that generates synthetic medical PDF reports for bulk upload testing |
| `generate_wearable_data.js` | Generates realistic wearable time-series payloads (steps, heart rate, sleep, SpO2) |
| `mock_doctor_roster.json` | Static roster of synthetic doctor accounts (name, specialty, assigned patients) |
| `mock_patient_detail.json` | Detailed synthetic patient profile with demographics, conditions, and lab history |
| `mock_report_extractions.json` | Pre-extracted lab result fixtures used for retrieval and alert tests |
| `wearable_payload.json` | Large (~2.6 MB) realistic wearable data payload for load / integration testing |
| `test-pdfs/` | Directory of pre-generated synthetic medical PDF files |
| `README.md` | Documents available mock data sets and how to use each script |
| `DELIVERY_MANIFEST.md` | Tracks which mock data artefacts have been delivered and their status |

---

## `sample_reports/` — Sample Medical PDF Reports

A collection of real-format (anonymised) medical PDF reports used during development for OCR and extraction testing.

---

## `types/` — Shared TypeScript Type Definitions

| File | Purpose |
|---|---|
| `api.ts` | TypeScript interface definitions for the primary API request/response shapes. Used by the frontend and Android app to ensure type-safe API calls. |

---

## Data Flow Summary

```
Patient uploads PDF
       ↓
 routes/upload.py  →  ocr/  →  extraction/pipeline.py
                                   ↓
                         Gemini extracts lab data
                                   ↓
                         lab_results table (Supabase)
                                   ↓
                 services/retrieval/indexer.py embeds chunks
                                   ↓
                         report_chunks table (pgvector)


Patient asks a question  →  routes/rag.py
       ↓
  [1] services/retrieval/  (pgvector → FAISS fallback)
  [2] services/context/data_fetchers.py  (labs, alerts, wearables, env, trends)
  [3] services/context/context_builder.py  →  BuiltContext
  [4] services/llm/gemini_service.py  →  AI answer
       ↓
  JSON response: {answer, context, chunks_retrieved, model}


Nightly cron  →  scripts/cron_nightly_alerts.py
                      ↓
              GET all active patients
                      ↓
              POST /alerts/admin/evaluate/{user_id}  (×N, concurrent)
                      ↓
              rules/engine.py  →  AlertRecord list
                      ↓
              rules/inserter.py  →  alerts + alert_evidence tables
```
