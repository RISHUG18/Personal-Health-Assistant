Tanush Garg

# Supabase PDF Uploading

## Functionalities
- Accepts PDF upload with `user_id` via `POST /reports/upload`
- Validates input, builds a unique storage path, uploads to Supabase Storage
- Returns storage path and public URL for client use

## Files involved
- [src/backend/main.py](src/backend/main.py): mounts the reports router
- [src/backend/routes/reports.py](src/backend/routes/reports.py): API endpoint for uploads
- [src/backend/controllers/reports_controller.py](src/backend/controllers/reports_controller.py): validation, path creation, storage upload
- [src/backend/config/supabase_client.py](src/backend/config/supabase_client.py): Supabase client + bucket config
- [src/backend/requirements.txt](src/backend/requirements.txt): dependencies (FastAPI, supabase, multipart)

## Flow (brief)
1) Client sends `user_id` + PDF file to `POST /reports/upload`.
2) Route reads file bytes and initializes Supabase client + bucket.
3) Controller validates input, builds unique path, uploads to Supabase Storage.
4) API responds with `path` and `public_url`.

# Context Object Schema (LLM)

## Functionalities
- Defines the context payload structure sent to the LLM
- Separates structured facts, alerts, environmental data, wearable data, and RAG chunks
- Enforces size constraints for chunking and total context

## Files involved
- [src/backend/contracts/context_schema.json](src/backend/contracts/context_schema.json): schema reference for the context object

## Required vs Optional (brief)
- Required: `meta.generated_at`, `meta.request_id`, `user_profile.user_id`, `user_profile.demographics.age`, `user_profile.demographics.gender`, `rag_knowledge_base.query_used`, and required fields inside each `retrieved_chunks` item.
- Optional: `name`, `medical_snapshot` fields, `wearable_data`, `active_alerts` entries, and `environmental_context` fields.

## Size constraints
- Max chunks: 10
- Max characters per chunk: 500
- Max total context characters: 4000

## Flow (brief)
1) Retrieval pipeline collects chunks + metadata.
2) Context builder injects structured facts, alerts, wearable, and environment blocks.
3) Payload is validated against the schema before LLM API call.

# LLM System Prompts

## Functionalities
- Defines user-facing and doctor-facing system prompts
- Enforces non-diagnostic, evidence-based responses
- Aligns output format with UI needs

## Files involved
- [src/backend/prompts/system_user.txt](src/backend/prompts/system_user.txt): user wellbeing coach prompt
- [src/backend/prompts/system_doctor.txt](src/backend/prompts/system_doctor.txt): doctor assistant prompt

## Flow (brief)
1) Context object is built from structured data + RAG chunks.
2) Appropriate system prompt is selected (user vs doctor).
3) LLM response is validated for format and safety rules.

# Mock RAG Retrieval Stub

## Functionalities
- Returns hardcoded RAG chunks for UI citation rendering
- Mimics Supabase Storage URLs for "open PDF" testing

## Files involved
- [src/backend/services/mock_retrieval.py](src/backend/services/mock_retrieval.py): mock retrieval service
- [src/backend/main.py](src/backend/main.py): test endpoint wiring

> Note: The production-oriented location is also available at
> `src/backend/services/retrieval/mock_retrieval.py`.

## Endpoint
- GET /api/v1/rag/test?user_id=...&query=...

## Flow (brief)
1) Frontend calls the test endpoint with `user_id` and `query`.
2) Service returns `rag_knowledge_base` payload with `retrieved_chunks`.
3) UI renders citations using `source_url` and `page_number`.

# Query Embedding 

## What it does

The query embedding module converts a user query (and/or document chunks) into dense vectors.
These vectors are intended to be used by the retrieval layer (FAISS/pgvector) for similarity search.

## Files involved (and responsibilities)

- [src/backend/services/embeddings/interfaces.py](src/backend/services/embeddings/interfaces.py)
	- Defines the `Embedder` protocol (interface) with `embed_query()` and `embed_texts()`.

- [src/backend/services/embeddings/sentence_transformer_embedder.py](src/backend/services/embeddings/sentence_transformer_embedder.py)
	- Concrete embedder using `sentence-transformers` (default: `BAAI/bge-base-en-v1.5`).
	- Provides implementations for `embed_query()` and `embed_texts()`.

- [src/backend/services/embeddings/query_embedding.py](src/backend/services/embeddings/query_embedding.py)
	- Convenience helpers:
		- `get_default_embedder()` (lazy singleton)
		- `embed_query(query)`
		- `embed_texts(texts)`
	- Supports env-based configuration:
		- `EMBEDDING_MODEL_NAME` (defaults to `BAAI/bge-base-en-v1.5`)
		- `EMBEDDING_NORMALIZE` (`true/false`, defaults to `true`)

- [src/backend/requirements.txt](src/backend/requirements.txt)
	- Includes the `sentence-transformers` dependency needed for embedding generation.

## Developer smoke test scripts

- [src/backend/scripts/embedding_smoke_test.py](src/backend/scripts/embedding_smoke_test.py)
	- Generates cleaned chunks from a fixture OCR text and prints embedding shape/sample.

- [src/backend/tests/fixtures/sample_ocr.txt](src/backend/tests/fixtures/sample_ocr.txt)
	- Fixture OCR text used by smoke tests.

## Usage (brief)

```python
from backend.services.embeddings.query_embedding import embed_query

vector = embed_query("What does my HbA1c mean?")
print(len(vector))
```

## Why this design is maintainable

- You can later plug in a different embedder (remote API, different local model, etc.) by implementing the same `Embedder` interface.
- The retrieval pipeline can accept an `Embedder` as a dependency (instead of hardcoding SentenceTransformers everywhere).

# Vector Similarity Retrieval (RAG — Production)

## What it does

Replaces the mock retrieval stub with real top-k cosine similarity search over stored report chunks.
Two strategies are supported:

- **pgvector** (default) — query hits a Postgres HNSW index via a Supabase RPC function; fast and production-ready.
- **FAISS** (fallback) — fetches stored embeddings from Supabase and searches locally in-memory; works without the pgvector extension.

OCR reports are automatically indexed on every `POST /reports/ocr` call — no separate step needed.

## Files involved (and responsibilities)

- [src/db/migrations/001_add_report_chunks.sql](src/db/migrations/001_add_report_chunks.sql)
	- Creates the `report_chunks` table (text, 768-dim vector column, HNSW index).
	- Defines the `match_report_chunks(query_embedding, user_id, top_k, threshold)` Postgres function called by the pgvector retriever.
	- Apply once in the Supabase SQL editor before using production retrieval.

- [src/backend/services/retrieval/indexer.py](src/backend/services/retrieval/indexer.py)
	- `index_report(report_id, user_id, ocr_text)` — runs the full pipeline: clean → chunk → embed → upsert into `report_chunks`.
	- Called automatically by the OCR controller after each successful OCR run.

- [src/backend/services/retrieval/pgvector_retrieval.py](src/backend/services/retrieval/pgvector_retrieval.py)
	- `retrieve_pgvector(user_id, query, top_k, match_threshold)` — embeds the query and calls the `match_report_chunks` Supabase RPC.
	- Returns ranked chunks with cosine similarity scores.

- [src/backend/services/retrieval/faiss_retrieval.py](src/backend/services/retrieval/faiss_retrieval.py)
	- `FaissRetriever` — reusable class: fetches stored embeddings once, builds a FAISS `IndexFlatIP`, and searches in-memory.
	- `retrieve_faiss(user_id, query, ...)` — one-shot convenience wrapper around `FaissRetriever`.
	- Useful for local development, tests, or when pgvector is unavailable.

- [src/backend/services/retrieval/\_\_init\_\_.py](src/backend/services/retrieval/__init__.py)
	- `retrieve_context(user_id, query, strategy="pgvector")` — unified entry-point; dispatches to pgvector or FAISS.
	- Returns `{"query_used": ..., "retrieved_chunks": [...]}` — same shape as the legacy mock, so callers need no changes.

- [src/backend/controllers/reports_controller.py](src/backend/controllers/reports_controller.py)
	- Updated to call `index_report` after every OCR persist (best-effort — indexing failures are logged, not raised).

- [src/backend/requirements.txt](src/backend/requirements.txt)
	- Added `faiss-cpu>=1.7` for local FAISS search.

## Flow (brief)

**Indexing (automatic on OCR):**
1. OCR text is stored in `medical_reports`.
2. Controller calls `index_report` → text is cleaned, chunked, embedded, and upserted into `report_chunks`.

**Retrieval (at query time):**
1. Caller invokes `retrieve_context(user_id, query)`.
2. Query is embedded with the same `BAAI/bge-base-en-v1.5` model.
3. pgvector HNSW index returns top-k chunks sorted by cosine similarity.
4. Results are returned as `retrieved_chunks` for context assembly before the LLM call.

## Usage (brief)

```python
from backend.services.retrieval import retrieve_context, index_report

# Retrieve (after chunks have been indexed)
result = retrieve_context(user_id="<uuid>", query="HbA1c levels")
for chunk in result["retrieved_chunks"]:
    print(chunk["relevance_score"], chunk["text_content"])

# Manual index (normally done automatically)
n = index_report(report_id="<uuid>", user_id="<uuid>", ocr_text=raw_text)

# Local FAISS fallback
result = retrieve_context(user_id="<uuid>", query="vitamin D", strategy="faiss")
```

## Design notes

- Cosine similarity is computed via inner product because embeddings are L2-normalised unit vectors — `1 - cosine_distance = dot_product`.
- `match_threshold` (default `0.4`) filters out low-relevance chunks before returning to the LLM context.
- FAISS index is not persisted; for repeated queries over the same user, keep a `FaissRetriever` instance alive rather than calling `retrieve_faiss` each time.

# Context Builder

## What it does

The context builder is the assembly layer between retrieval and the LLM.  It gathers all relevant data (RAG chunks, lab results, alerts, vitals, environment, wearables) and packages it into a single validated `BuiltContext` object — the exact payload that the Gemini prompt layer will consume.

It does **nothing** else:

- Does not fetch from the DB (see `data_fetchers.py`)
- Does not embed queries (see `services/embeddings/`)
- Does not call Gemini (future `services/llm/`)

This separation keeps each layer independently testable and swappable.

## Files involved (and responsibilities)

- [src/backend/services/context/context_builder.py](src/backend/services/context/context_builder.py)
	- Pydantic models: `BuiltContext`, `UserProfile`, `MedicalSnapshot`, `WearableData`, `AlertItem`, `EnvironmentalContext`, `RagKnowledgeBase`, `ContextMeta`, `RetrievedChunk`.
	- `build_context(query, user_id, retrieved_chunks, ...)` — pure assembly function; validates all inputs via Pydantic; applies size controls (max 10 chunks, 500 chars/chunk, 4000 chars total).
	- `BuiltContext` now has a top-level `structured_facts` field (list of raw lab-result dicts from `lab_results`); previously `raw_lab_results` from `fetch_user_lab_snapshot()` was fetched but silently dropped.

- [src/backend/services/context/data_fetchers.py](src/backend/services/context/data_fetchers.py)
	- `fetch_active_alerts(user_id)` — queries the `alerts` table for open alerts.
	- `fetch_user_lab_snapshot(user_id)` — queries `lab_results` (joined to `medical_reports`) and maps known test names to the `recent_vitals` block.
	- `fetch_user_profile(user_id)` — queries the `users` table (fields: `full_name`, `date_of_birth`, `gender`, `weight_kg`, `height_cm`) for user demographics; returns mapped `name`, `gender`, `weight_kg`, `height_cm`.
	- All fetchers return empty dicts/lists on failure — never block the pipeline.

- [src/backend/services/context/\_\_init\_\_.py](src/backend/services/context/__init__.py)
	- Re-exports `build_context` and `BuiltContext` as the package's public API.

- [src/backend/routes/rag.py](src/backend/routes/rag.py)
	- `POST /api/v1/rag_query` — full pipeline endpoint: retrieval → data fetching → context assembly → returns structured context.
	- Accepts `user_id`, `query`, `role` (`"user"` / `"doctor"`), `retrieval_strategy`, `top_k`, `match_threshold`, and optional `environment` / `wearable_data` blocks.

- [src/backend/main.py](src/backend/main.py)
	- Mounts the `rag` router alongside `reports`.

## Flow (brief)

```
POST /api/v1/rag_query  {user_id, query}
        │
        ├─ retrieve_context()            ← vector search (pgvector / FAISS)
        ├─ fetch_active_alerts()         ← alerts table
        ├─ fetch_user_lab_snapshot()     ← lab_results + medical_reports
        ├─ fetch_user_profile()          ← stub (demographics)
        │
        └─ build_context()
                │
                ├─ validate all inputs (Pydantic)
                ├─ trim chunks: max 10, max 500 chars each, max 4000 chars total
                ├─ normalise alert keys (reason ↔ message, severity lowercase)
                ├─ lift raw_lab_results → structured_facts (top-level)
                └─ return BuiltContext
```

## Usage (brief)

```python
from backend.services.context import build_context
from backend.services.context.data_fetchers import fetch_active_alerts, fetch_user_lab_snapshot
from backend.services.retrieval import retrieve_context

chunks   = retrieve_context(user_id, query)["retrieved_chunks"]
alerts   = fetch_active_alerts(user_id)
snapshot = fetch_user_lab_snapshot(user_id)

context = build_context(
    query=query,
    user_id=user_id,
    retrieved_chunks=chunks,
    alerts=alerts,
    medical_snapshot=snapshot,
    environment={"aqi_level": 120, "location_city": "Delhi"},
    role="user",
)

payload = context.model_dump()   # → pass to prompt builder / Gemini
```

## Design notes

- `build_context` is a **pure function**: no I/O, no side effects.  The same inputs always produce the same output, making it trivial to unit-test.
- Size controls are enforced inside the builder, not at the route layer, so any caller benefits automatically.
- The `role` field (`"user"` / `"doctor"`) flows through to the context object so the prompt layer can select between `system_user.txt` and `system_doctor.txt` without extra logic.
- Fetcher failures degrade gracefully: an alert-fetch failure produces `alerts=[]`, not a 500 error.
- `structured_facts` is populated from `fetch_user_lab_snapshot()`'s `raw_lab_results` key.  It is kept as a list of plain dicts (not a typed Pydantic model) so new test types from the DB require no model change.

# Gemini LLM Service

## What it does

The LLM service is the final stage of the RAG pipeline.  It takes the fully
assembled `BuiltContext` payload, serialises it to a structured JSON prompt,
and calls the Gemini API to produce a grounded, evidence-based natural-language
response.

Two key safety properties are enforced at this layer:

- **Low temperature (0.1)** — forces Gemini to stay close to the data provided, minimising hallucinations.
- **Strict system prompt separation** — the role-specific behavioural rules (`system_instruction`) are passed as a separate `GenerateContentConfig` argument, not concatenated into the user turn, which makes prompt injection far harder.
- **File-driven citation instructions** — grounding rules live in plain text files (`prompts/citation_user.txt`, `prompts/citation_doctor.txt`) so wording can be updated without a code deploy.

## Files involved (and responsibilities)

### Prompt files (`prompts/`)

- [src/backend/prompts/system_user.txt](src/backend/prompts/system_user.txt)
	- Behavioural rules for the wellbeing-coach persona: safety rules, output format, tone.
	- Passed to `GenerateContentConfig.system_instruction` — hard constraint, not input data.

- [src/backend/prompts/system_doctor.txt](src/backend/prompts/system_doctor.txt)
	- Behavioural rules for the clinical-assistant persona: evidence-first, citation-mandatory, no fluff.

- [src/backend/prompts/citation_user.txt](src/backend/prompts/citation_user.txt)
	- Citation instructions for the user (wellbeing coach) role.
	- Defines how to cite report chunks (`[Report: <filename>]`) and lab values (`[Lab: <test_name> — <value> <unit>]`).
	- Uses plain, friendly language matching the user persona.

- [src/backend/prompts/citation_doctor.txt](src/backend/prompts/citation_doctor.txt)
	- Citation instructions for the doctor (clinical assistant) role.
	- Requires full inline citations with reference ranges (`[Source: <filename>, chunk <chunk_id>]`, `[Lab: <test_name>, <value> <unit>, ref <range>]`) and trend annotations.
	- Stricter format to support clinical traceability.

### Service files

- [src/backend/services/llm/interfaces.py](src/backend/services/llm/interfaces.py)
	- `LLMProvider` — a `@runtime_checkable` `Protocol` that any LLM back-end must implement.
	- The route and any other caller depend **only** on this interface (Dependency Inversion Principle).
	- Swapping Gemini for a different back-end (OpenAI, local Ollama, …) requires creating a new class implementing this protocol — no other file changes needed (Open/Closed Principle).

- [src/backend/services/llm/prompt_builder.py](src/backend/services/llm/prompt_builder.py)
	- `_PROMPT_FILES` / `_CITATION_FILES` — role → filename registries. Adding a new role = add one entry to each dict + create two files.
	- `_load_prompt_file(filepath)` — shared private loader with `@lru_cache`; keeps one copy of each file in memory per process, shared by both loaders.
	- `load_system_prompt(role)` — loads `prompts/system_<role>.txt`; used by `rag.py` to build the `GenerateContentConfig`.
	- `load_citation_instructions(role)` — loads `prompts/citation_<role>.txt`; injected by `build_prompt()` into the user turn.
	- `build_prompt(query, context_dict)` — assembles the full user-turn string; extracts `role` from `context_dict["role"]` (set by `build_context()`); injects citation block only when grounding data is present; best-effort (missing citation file logs a warning and is skipped, not a fatal error).
	- Single Responsibility: this module owns **structure** and **conditional logic** only — all wording lives in the prompt files.

- [src/backend/services/llm/gemini_service.py](src/backend/services/llm/gemini_service.py)
	- `GeminiService` — concrete `LLMProvider` backed by `google-genai`.
	- Initialises a single `genai.Client` at construction time (reads `GEMINI_API_KEY` from env), so API-key validation fails at startup rather than on the first request.
	- `generate(query, context_dict, system_instruction)` — delegates prompt building to `build_prompt`, configures `temperature=0.1` and the system instruction, calls `client.models.generate_content`, and raises `RuntimeError` (never returns `None`) on empty or blocked responses.
	- `_extract_finish_reason(response)` — safe helper that extracts `finish_reason` for debugging without crashing on SDK version differences.

- [src/backend/services/llm/\_\_init\_\_.py](src/backend/services/llm/__init__.py)
	- Re-exports `GeminiService`, `LLMProvider`, `load_system_prompt`, `load_citation_instructions`, and `build_prompt` as the package's public API.

- [src/backend/routes/rag.py](src/backend/routes/rag.py)
	- `POST /api/v1/rag_query` — the route completes all four pipeline stages: retrieval → data fetching → context assembly → Gemini generation.
	- `_llm = GeminiService()` is instantiated once at module load (process-level singleton) to avoid recreating the client on every request.
	- On Gemini `RuntimeError`, substitutes a `_FALLBACK_ANSWER` string instead of returning HTTP 502, so the frontend can still display the assembled context.
	- Response body includes `answer`, `context`, `chunks_retrieved`, `grounding_available`, `model`, and `llm_error`.

- [src/backend/requirements.txt](src/backend/requirements.txt)
	- `google-genai>=1.0` for the Gemini Python SDK.

## Flow (complete 4-stage pipeline)

```
POST /api/v1/rag_query  {user_id, query, role, ...}
        │
        ├─ 1. retrieve_context()           ← pgvector / FAISS top-k search
        ├─ 2. fetch_active_alerts()        ← alerts table
        │    fetch_user_lab_snapshot()     ← lab_results + medical_reports
        │    fetch_user_profile()          ← user demographics stub
        │
        ├─ 3. build_context()
        │       ├─ validate all inputs (Pydantic)
        │       ├─ trim chunks: max 10, max 500 chars each, max 4000 total
        │       └─ return BuiltContext
        │
        └─ 4. GeminiService.generate()
                ├─ load_system_prompt(role)     ← prompts/system_user.txt or
                │                                  prompts/system_doctor.txt
                ├─ build_prompt(query, ctx)
                │       ├─ JSON context block
                │       ├─ load_citation_instructions(role)  [if grounding data present]
                │       │       └─ prompts/citation_user.txt  or
                │       │           prompts/citation_doctor.txt
                │       └─ USER QUERY label + query
                ├─ GenerateContentConfig(
                │       system_instruction=...,
                │       temperature=0.1)
                └─ client.models.generate_content(...)
                        └─ return answer (markdown)
```

## Usage (brief)

```python
# Direct service usage (e.g., in a script or test)
from backend.services.llm import GeminiService, load_system_prompt

llm = GeminiService()                          # reads GEMINI_API_KEY from env
system_prompt = load_system_prompt(role="user")

answer = llm.generate(
    query="Why is my iron low?",
    context_dict=context.model_dump(),         # BuiltContext dict
    system_instruction=system_prompt,
)
print(answer)
```

```bash
# Full pipeline via API (server must be running with GEMINI_API_KEY set)
curl -X POST http://localhost:8000/api/v1/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<uuid>",
    "query": "Why is my ferritin low even though I eat well?",
    "role": "user"
  }'
# Response:
# {
#   "answer": "...",              ← Gemini response (cites chunk_id / lab test)
#   "context": {...},             ← full BuiltContext including structured_facts
#   "chunks_retrieved": 3,
#   "grounding_available": true,  ← false when no report chunks were retrieved
#   "model": "gemini-3.1-pro",
#   "llm_error": null             ← non-null only when Gemini failed and fallback used
# }
```

## Environment setup

```bash
# Install the Google Gemini SDK
pip install google-genai>=1.0

# Add to .env (already included in src/backend/.env)
GEMINI_API_KEY="your-key-here"
```

## Design notes

- **Model choice (`gemini-3.1-pro`)**: handles structured JSON context reliably.
- **Temperature `0.1`**: for a medical assistant, "creativity" = hallucination risk.  Values between `0.0` and `0.2` force the model to reason strictly from the provided data.
- **JSON serialisation (`json.dumps(indent=2)`)**: indented JSON is more reliably parsed by the model than free-form text when the payload contains nested keys like `active_alerts` and `retrieved_chunks`.
- **System prompt separation**: passing the system instruction as `GenerateContentConfig.system_instruction` (not prepended to the user turn) ensures the model treats it as a hard behavioural constraint, not just another input token.
- **Process-level singleton**: `_llm = GeminiService()` at import time means one `genai.Client` per worker process — connection overhead is paid once, not per request.
- **Safety-filter guard**: if Gemini returns an empty response (e.g., safety block), a `RuntimeError` is raised with the `finish_reason` so operators can diagnose issues from logs.

---

## Context Builder Update

`BuiltContext` now contains all three required blocks:

```json
{
  "active_alerts":     [...],   ← alerts from the alerts table (AlertItem list)
  "rag_knowledge_base": {
    "retrieved_chunks": [...]   ← top-k RAG chunks from vector search
  },
  "structured_facts":  [...]    ← raw lab-result rows from lab_results table
}
```

**What changed:**
- Added `structured_facts: List[Dict[str, Any]]` field to `BuiltContext` (top-level, not nested).
- `build_context()` now extracts `raw_lab_results` from the `medical_snapshot` dict (returned by `fetch_user_lab_snapshot()`) and populates this field.  Previously `raw_lab_results` was fetched from the DB but silently discarded.
- Each entry in `structured_facts` contains: `test_name`, `value`, `unit`, `reference_range`, `abnormal_flag`.

**Files changed:** [src/backend/services/context/context_builder.py](src/backend/services/context/context_builder.py)

---

## Response Grounding

Gemini responses are now explicitly instructed to cite their sources using role-appropriate language. Citation instructions live in plain text files so they can be updated without a code change.

**New files:**

- [src/backend/prompts/citation_user.txt](src/backend/prompts/citation_user.txt) — friendly, plain-language rules for the wellbeing-coach role.
  - Report chunks → `[Report: <source_filename>]` (hides raw `chunk_id` from the user)
  - Lab values → `[Lab: <test_name> — <value> <unit>]` with `⚠️` for abnormal flags

- [src/backend/prompts/citation_doctor.txt](src/backend/prompts/citation_doctor.txt) — formal, clinical rules for the doctor role.
  - Report chunks → `[Source: <source_filename>, chunk <chunk_id>]` (exposes `chunk_id` for clinical traceability)
  - Lab values → `[Lab: <test_name>, <value> <unit>, ref <reference_range>]` with `**⚠️**` for abnormal flags
  - Trend annotations required when multiple time-stamped values exist

**What changed in `prompt_builder.py`:**

- Added `_CITATION_FILES` registry (role → filename) — symmetric with the existing `_PROMPT_FILES` registry.
- Added `load_citation_instructions(role)` — same `@lru_cache` pattern as `load_system_prompt()`; reads from disk once per process.
- Added private `_load_prompt_file(filepath)` as the shared cached inner loader used by both loaders; removes code duplication.
- Added `_resolve_role()` helper — centralises unknown-role fallback logic for both registries.
- `build_prompt()` now extracts `role` from `context_dict["role"]` (already set by `build_context()`), calls `load_citation_instructions(role)`, and injects the result as a `--- CITATION INSTRUCTIONS ---` block when grounding data is present. If the file is missing, a warning is logged and the block is skipped (best-effort; never fatal).

**Files changed:** [src/backend/services/llm/prompt_builder.py](src/backend/services/llm/prompt_builder.py), [src/backend/services/llm/\_\_init\_\_.py](src/backend/services/llm/__init__.py)

---

## Error Handling

All three failure modes are handled:

| Failure | Previous behaviour | New behaviour |
|---|---|---|
| **Gemini API failure** | HTTP 502 | Returns `_FALLBACK_ANSWER` string + `llm_error` field; always HTTP 200 so the UI can still render the context |
| **Empty retrieval** | No signal | `grounding_available: false` in response body; LLM still called with available data |
| **Invalid query** | Empty string → 422; whitespace-only → 500; too-short → no check | All invalid queries → 422: empty, whitespace-only, and `len < 3` all rejected before any work is done; `ValueError` from `build_context()` is also mapped to 422 |

**Response body changes:**

```json
{
  "answer": "...",                  ← fallback text substituted on Gemini failure
  "context": {...},
  "chunks_retrieved": 3,
  "grounding_available": true,       ← false when no RAG chunks returned
  "model": "gemini-3.1-pro",
  "llm_error": null                  ← error message string on Gemini failure
}
```

---

## Environmental Data Integration (Open-Meteo)

### What was built

A self-contained `services/environment/` package that chains three free Open-Meteo API calls into a single cached snapshot, which is stored in Supabase and injected into the Gemini context automatically.

### Why it exists

The `EnvironmentalContext` block in `BuiltContext` was already part of the context schema (city, AQI, temperature, weather condition) but was always `null` unless the API caller manually provided the data.  This integration fills that block automatically by fetching live data whenever a city is known.

The LLM can then give contextually aware answers, e.g.:

> *"Given Delhi's current AQI of 175 (Unhealthy) and your mild asthma, you should avoid outdoor exercise today."*

---

### Architecture 

```
services/environment/
    __init__.py        ← public API: get_environment_service(), EnvironmentalSnapshot
  models.py          ← DTOs: WeatherSnapshot, AirQualitySnapshot,
                           EnvironmentalSnapshot (with to_context_dict())
  interfaces.py      ← Protocols: IWeatherClient,
                           IAirQualityClient, IEnvironmentStore
  fetchers.py        ← Concrete: OpenMeteoWeatherFetcher,
                           OpenMeteoAQIFetcher
    store.py           ← Concrete: SupabaseEnvironmentStore, NullEnvironmentStore
    service.py         ← Orchestrator: EnvironmentService + get_environment_service()
```

---

### Coordinate-first API chain

```
user_lat, user_lon
  │
  ├──────────────────────────────────────┐
  ▼                                      ▼
OpenMeteoWeatherFetcher                 OpenMeteoAQIFetcher
  .fetch_weather(lat, lon)                .fetch_aqi(lat, lon)
  GET api.open-meteo.com/v1/forecast      GET air-quality-api.open-meteo.com/v1/air-quality
    ?current=temperature_2m,              ?current=us_aqi
             relative_humidity_2m,
             weather_code
  → WeatherSnapshot                     → AirQualitySnapshot(us_aqi)
    │
    ▼
  WMO code → _wmo_to_label(code) → "Clear sky" / "Moderate rain" / …
    │
    └──────────────┬───────────────────────┘
                   ▼
            EnvironmentalSnapshot
             .location_city
             .latitude / .longitude
             .temperature_celsius
             .humidity_percent
             .aqi_level
             .weather_condition
             .weather_code
             .fetched_at
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
SupabaseEnvironmentStore    .to_context_dict()
  INSERT INTO               → {"location_city", "aqi_level",
  environmental_data           "temperature_celsius",
                               "weather_condition"}
                                     │
                                     ▼
                               build_context(environment=...)
                                     │
                                     ▼
                               EnvironmentalContext in BuiltContext
                                     │
                                     ▼
                               Gemini LLM prompt
```

---

### Database schema (migration 005)

```sql
CREATE TABLE environmental_data (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID REFERENCES public.users(id) ON DELETE CASCADE,
    location_city        TEXT NOT NULL,
    latitude             NUMERIC,
    longitude            NUMERIC,
    temperature_celsius  NUMERIC,
    humidity_percent     NUMERIC,
    aqi_level            INTEGER,          -- US AQI 0–500
    weather_condition    TEXT,             -- human-readable, e.g. "Partly cloudy"
    weather_code         INTEGER,          -- raw WMO code
    recorded_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_env_user_time ON environmental_data(user_id, recorded_at DESC);
CREATE INDEX idx_env_city_time ON environmental_data(location_city, recorded_at DESC);
```

**Run:** paste `src/db/migrations/005_add_environmental_data.sql` into the Supabase SQL editor.

---

### Route integration (`POST /api/v1/rag_query`)

The `rag.py` route now resolves environmental data in **Step 2b**, inserted between structured data fetching (Step 2) and context assembly (Step 3):

```
Request body environment resolution order
────────────────────────────────────────
  Inputs used:
    • body.environment      (optional manual override/live city payload)
    • body.user_location    (optional GPS-derived city label from frontend)
    • body.user_lat         (optional GPS latitude)
    • body.user_lon         (optional GPS longitude)

  1. user_lat + user_lon provided    → call EnvironmentService.get_snapshot_for_coordinates(...)
                                        • skips geocoding entirely
                                        • fetches weather + AQI directly by coordinates
                                        • caches row to environmental_data table
  2. else if environment has fields  → use body.environment directly (manual override)
  3. else                            → fetch_cached_environment(
                                          user_id,
                                          current_lat=user_lat,
                                          current_lon=user_lon,
                                          current_gps_city=user_location
                                        )
                                        • if coordinate drift > threshold: return None
                                        • else if coordinates absent and city mismatch: return None
                                        • else return cached row
```

The resolved `env_data` dict is then passed to `build_context(environment=env_data)`.

This adds a deterministic location-mismatch safety net before the prompt is built: stale AQI/weather from an old city is blocked at the backend layer and never sent to Gemini.

---

### New helper: `fetch_cached_environment`

Added to `services/context/data_fetchers.py`.  Reads the most recent row from `environmental_data` for a given user and now supports a deterministic city consistency check.

Current behaviour:

- Primary check (recommended): if `current_lat/current_lon` are provided,
  compare against cached `latitude/longitude`.  Cache is invalidated when
  either absolute difference exceeds `0.05` degrees (~5–6 km).
- Secondary fallback: if coordinates are absent, use city-string mismatch
  invalidation (`current_gps_city` vs cached `location_city`).
- If neither coordinates nor city label are provided, behaves as a latest-row
  cache fallback.

This follows the safety principle: missing environment data is safer than wrong environment data.

---

### Frontend API contract update (recommended)

Send coordinates on every `POST /api/v1/rag_query` call:

```json
{
  "user_id": "<uuid>",
  "query": "Should I go for a run today?",
  "user_lat": 17.4065,
  "user_lon": 78.4772,
  "user_location": "Hyderabad"
}
```

Notes:

- `user_lat` and `user_lon` must be sent together (backend validates this).
- `user_location` is optional and treated only as a human-readable label /
  fallback check.
- Coordinate-first flow removes one API call (geocoding), improves latency,
  and avoids duplicate-city ambiguity.

---

### Prompt safety update for missing environment data

Both system prompts were updated to explicitly forbid environment guessing:

- `prompts/system_user.txt`
- `prompts/system_doctor.txt`

New rule: if environment context is missing/null, the assistant must explicitly state local environment data is unavailable and avoid weather/AQI-based recommendations.

---

### Files changed

| File | Change |
|---|---|
| `src/db/migrations/005_add_environmental_data.sql` | New — creates `environmental_data` table + two indexes |
| `src/backend/services/environment/__init__.py` | New — package public API |
| `src/backend/services/environment/models.py` | New — `WeatherSnapshot`, `AirQualitySnapshot`, `EnvironmentalSnapshot` |
| `src/backend/services/environment/interfaces.py` | New — `IWeatherClient`, `IAirQualityClient`, `IEnvironmentStore` protocols |
| `src/backend/services/environment/fetchers.py` | New — `OpenMeteoWeatherFetcher`, `OpenMeteoAQIFetcher` + WMO code table |
| `src/backend/services/environment/store.py` | New — `SupabaseEnvironmentStore`, `NullEnvironmentStore` |
| `src/backend/services/environment/service.py` | New — `EnvironmentService` coordinate-first orchestrator + `get_environment_service()` factory |
| `src/backend/services/context/data_fetchers.py` | Added `fetch_cached_environment()` with coordinate drift invalidation (`current_lat/current_lon`) and city fallback check |
| `src/backend/routes/rag.py` | Added Step 2b environment resolution, `_env_service` singleton, `user_location` plus `user_lat/user_lon` request fields |
| `src/backend/prompts/system_user.txt` | Added explicit rule for missing/null environment context |
| `src/backend/prompts/system_doctor.txt` | Added explicit rule for missing/null environment context |
| `src/backend/requirements.txt` | Added `httpx>=0.27,<1.0` |

**Files changed:** [src/backend/routes/rag.py](src/backend/routes/rag.py)

---

# Wearable Vitals Pipeline (Person 3)

## What it does

The wearable vitals pipeline enables high-frequency continuous data ingestion from fitness bands and wearable devices, stores it in a time-series optimized table, and provides 7-day aggregated summaries for the AI context builder.

Key features:

- **Batch ingestion**: Accept arrays of vital readings via a single API call
- **Time-series storage**: EAV (Entity-Attribute-Value) pattern supports any metric type
- **7-day aggregation**: RPC function computes avg/min/max/latest for context builder
- **Auto-fetch in RAG**: Wearable vitals are automatically fetched during `/api/v1/rag_query`

---

## Architecture

```
POST /api/v1/ingest/vitals
    │
    ├─ VitalsBatch (Pydantic validation)
    │       └─ List[VitalReading]
    │
    └─ WearableService.ingest_batch()
            │
            └─ SupabaseVitalsStore.insert_batch()
                    │
                    └─ INSERT INTO wearable_vitals (upsert, skip duplicates)


GET /api/v1/vitals/{user_id}/summary
    │
    └─ WearableService.get_vitals_summary()
            │
            └─ SupabaseVitalsStore.get_summary()
                    │
                    └─ RPC: get_vitals_summary(user_id, days)
                            │
                            └─ Returns aggregated metrics
                                    │
                                    └─ VitalsSummary.to_context_dict()
                                            │
                                            └─ Ready for build_context(wearable_data=...)
```

---

## Database Schema (Migration 006)

```sql
CREATE TABLE wearable_vitals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    recorded_at     TIMESTAMP WITH TIME ZONE NOT NULL,
    metric_type     TEXT NOT NULL,
    value           NUMERIC NOT NULL,
    unit            TEXT,
    device_id       TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT unique_user_metric_time UNIQUE (user_id, recorded_at, metric_type)
);

-- Indexes for efficient time-range queries
CREATE INDEX idx_vitals_user_time ON wearable_vitals (user_id, recorded_at DESC);
CREATE INDEX idx_vitals_user_metric_time ON wearable_vitals (user_id, metric_type, recorded_at DESC);
```

**Supported metric types:**
- `heart_rate` (bpm)
- `resting_heart_rate` (bpm)
- `steps` (count)
- `sleep_minutes` (min)
- `deep_sleep_minutes` (min)
- `sleep_score` (0-100)
- `calories_burned` (kcal)
- `active_minutes` (min)
- `hrv_ms` (ms)
- `spo2` (%)

**Run:** Apply `src/db/migrations/006_add_wearable_vitals.sql` in the Supabase SQL editor.

---

## API Endpoints

### POST /api/v1/ingest/vitals

Batch ingest vital readings from wearable devices.

**Request:**
```json
{
  "user_id": "<uuid>",
  "readings": [
    {
      "recorded_at": "2024-01-15T10:30:00Z",
      "metric_type": "heart_rate",
      "value": 72,
      "unit": "bpm",
      "device_id": "fitbit_abc123"
    },
    {
      "recorded_at": "2024-01-15T10:30:00Z",
      "metric_type": "steps",
      "value": 5432,
      "unit": "steps"
    }
  ]
}
```

**Response:**
```json
{
  "user_id": "<uuid>",
  "inserted": 2,
  "skipped": 0,
  "total": 2,
  "errors": []
}
```

### GET /api/v1/vitals/{user_id}/summary

Get aggregated 7-day vitals summary for the context builder.

**Query parameters:**
- `days` (default: 7, max: 30) — Number of days to aggregate

**Response:**
```json
{
  "user_id": "<uuid>",
  "period_days": 7,
  "metric_count": 5,
  "summary": {
    "heart_rate": {"avg": 72.5, "min": 58, "max": 120, "latest": 68, "samples": 1440, "unit": "bpm"},
    "steps": {"avg": 8500, "min": 2000, "max": 15000, "latest": 10234, "samples": 7, "unit": "steps"}
  },
  "wearable_context": {
    "device_synced_at": "2024-01-15T10:30:00Z",
    "activity_summary": {...},
    "sleep_metrics": {...},
    "heart_health": {...},
    "vitals_7day_summary": {...}
  }
}
```

The `wearable_context` field is ready to pass directly to `build_context(wearable_data=...)`.

---

## Context Builder V2 Integration (Main Pipeline)

**The wearable vitals are now automatically integrated into the main RAG pipeline for both `user` and `doctor` roles.**

The RAG pipeline now automatically fetches wearable vitals:

```
POST /api/v1/rag_query
    │
    ├─ Step 1: Retrieval (pgvector/FAISS)
    ├─ Step 2: Data fetching (alerts, lab results, profile)
    ├─ Step 2b: Environmental data
    ├─ Step 2c: Wearable vitals ← NEW
    │       │
    │       └─ fetch_wearable_vitals(user_id, days=7)
    │               │
    │               └─ Returns dict compatible with WearableData model
    │
    ├─ Step 3: Context assembly
    │       │
    │       └─ build_context(..., wearable_data=auto_fetched)
    │
    └─ Step 4: LLM generation (user or doctor role)
            │
            └─ Gemini uses vitals_7day_summary to give context-aware health advice
```

**Priority order for wearable data:**
1. If `body.wearable_data` is provided → use as-is (manual override)
2. If `body.wearable_data` is None → auto-fetch from `wearable_vitals` table

**Updated system prompts:**
- `src/backend/prompts/system_user.txt` now instructs the AI to use 7-day trends for personalized wellbeing advice
- `src/backend/prompts/system_doctor.txt` now instructs the AI to correlate wearable trends with lab results for clinical insights
- Both `citation_user.txt` and `citation_doctor.txt` updated with wearable citation formats

**Example AI responses using wearable data:**

*User role (wellbeing coach):*
> "Your resting heart rate has been a bit high this week [7-day avg: 78 bpm], and your sleep hours are trending down [7-day range: 5.2-7.8 hrs]. This might explain why you're feeling more tired. Try aiming for 7.5 hours tonight and see if that helps bring your HR back to your baseline."

*Doctor role (clinical assistant):*
> "Resting HR elevated [7-day avg: 78 bpm, range 68-92 bpm] with declining HRV trend [42ms → 34ms over 7 days]. Combined with HbA1c at 6.8% [Lab: Hemoglobin A1c, 6.8%, ref 4.0-5.6] **⚠️** and suboptimal sleep [7-day avg: 5.8 hrs], glycemic control may be compounded by inadequate recovery. Recommend sleep hygiene assessment and consider CGM monitoring."

---

## Optional: Summarizer Role (Separate Use Case)

For specialized use cases requiring concise 3-bullet summaries (e.g., physician morning briefs), a dedicated `summarizer` role is available:

**Prompt files:**
- `src/backend/prompts/system_summarizer.txt` — 3-bullet summary instructions
- `src/backend/prompts/citation_summarizer.txt` — Citation format for summaries

**Usage:**
```python
from backend.services.llm import load_system_prompt

# For a 3-bullet summary (optional, separate from main pipeline)
system_prompt = load_system_prompt(role="summarizer")
```

**Note:** This is NOT the primary integration. The main improvement is that the `user` and `doctor` roles now have access to wearable vitals in the standard RAG pipeline.

**Example output (summarizer role):**
```
- **Heart rate variability decreased 18% over 7 days** (avg 42ms → 34ms),
  coinciding with elevated resting HR (avg 78 bpm). May indicate autonomic stress.
- **Sleep efficiency suboptimal**: Deep sleep averaged 62 min/night (target: 90+),
  with sleep score declining from 78 to 65.
- **Step count below baseline** (avg 4,200 vs typical 7,500) with active minutes
  at 23 min/day. Combined with fatigue alert, recommend metabolic assessment.
```

---

## Files Created/Modified

| File | Change |
|------|--------|
| `src/db/migrations/006_add_wearable_vitals.sql` | New — time-series table + RPC function |
| `src/backend/services/wearable/__init__.py` | New — package public API |
| `src/backend/services/wearable/models.py` | New — VitalReading, VitalsBatch, VitalsSummary DTOs |
| `src/backend/services/wearable/interfaces.py` | New — IVitalsStore, IVitalsAggregator protocols |
| `src/backend/services/wearable/store.py` | New — SupabaseVitalsStore, NullVitalsStore |
| `src/backend/services/wearable/service.py` | New — WearableService + factory |
| `src/backend/routes/vitals.py` | New — /ingest/vitals, /vitals/{user_id}/summary endpoints |
| `src/backend/services/context/data_fetchers.py` | Added `fetch_wearable_vitals()` |
| `src/backend/services/context/context_builder.py` | Added `vitals_7day_summary` to WearableData model |
| `src/backend/routes/rag.py` | Added Step 2c for auto-fetching wearable vitals |
| `src/backend/prompts/system_user.txt` | **Updated:** Added 7-day vitals to INPUT DATA, added trend usage examples |
| `src/backend/prompts/system_doctor.txt` | **Updated:** Added 7-day vitals to INPUT DATA, added clinical correlation guidance |
| `src/backend/prompts/citation_user.txt` | **Updated:** Added wearable vitals citation formats |
| `src/backend/prompts/citation_doctor.txt` | **Updated:** Added clinical wearable vitals citation formats |
| `src/backend/services/llm/prompt_builder.py` | Added `summarizer` role to registries (optional) |
| `src/backend/prompts/system_summarizer.txt` | New — 3-bullet summary system prompt (optional) |
| `src/backend/prompts/citation_summarizer.txt` | New — citation format for summarizer (optional) |
| `src/backend/main.py` | Mounted vitals router |
| `src/db/migrations/007_vitals_cleanup_job.sql` | **New** — Wearable vitals cleanup via pg_cron |
| `src/db/migrations/008_environmental_cleanup_job.sql` | **New** — Environmental cache cleanup via pg_cron |

---

# Automated Data Retention (Migrations 007 & 008)

## What it does

Implements tiered data retention using PostgreSQL's native `pg_cron` scheduler. Raw high-frequency wearable data and short-term environmental cache have diminishing value over time. These migrations automate cleanup to prevent storage bloat.

## Retention Strategy

```
┌─────────────────────────────────────────────────────────────┐
│  TIERED RETENTION VIA SUMMARIZATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Raw Wearable Vitals:    30 days (hot storage buffer)       │
│  ├─ Allows offline device sync recovery                     │
│  └─ Provides window for weekly AI summary generation        │
│                                                              │
│  Environmental Cache:     3 days (API cache buffer)         │
│  └─ Weather/AQI older than 3 days is outdated              │
│                                                              │
│  AI Summaries:           ∞ (permanent medical record)       │
│  └─ 3-bullet summaries become lifetime patient narrative    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Automated Cleanup Jobs

| Job Name | Schedule | Target Table | Retention | Migration | Purges |
|----------|----------|--------------|-----------|-----------|--------|
| `purge-stale-wearable-vitals` | Daily 3:00 AM UTC | `wearable_vitals` | 30 days | 007 | `recorded_at < NOW() - INTERVAL '30 days'` |
| `purge-stale-environment-data` | Daily 4:00 AM UTC | `environmental_data` | 3 days | 008 | `recorded_at < NOW() - INTERVAL '3 days'` |

## Implementation

**Files:**
- `src/db/migrations/007_vitals_cleanup_job.sql` — Wearable vitals cleanup
- `src/db/migrations/008_environmental_cleanup_job.sql` — Environmental cache cleanup

**Apply in Supabase SQL editor:**
1. Enable `pg_cron` extension (one-time setup, done in migration 007)
2. Run migration 007 to schedule wearable vitals cleanup
3. Run migration 008 to schedule environmental data cleanup
4. Verify with: `SELECT jobid, jobname, schedule, active FROM cron.job;`

**Expected output:**
```
jobid |          jobname             |  schedule  | active
------+------------------------------+------------+--------
  1   | purge-stale-wearable-vitals  | 0 3 * * *  | t
  2   | purge-stale-environment-data | 0 4 * * *  | t
```

**Why pg_cron?**
- **Database Native**: Runs inside Postgres engine, no external orchestration
- **Zero Backend Load**: Python server doesn't waste CPU on cleanup
- **Reliable**: Automatic execution, no human intervention required
- **Cost Effective**: Prevents storage bloat on Supabase free/pro tiers

## Manual Management

**Check scheduled jobs:**
```sql
SELECT jobid, jobname, schedule, active FROM cron.job;
```

**Disable a job (without dropping migration):**
```sql
SELECT cron.unschedule('purge-stale-wearable-vitals');
SELECT cron.unschedule('purge-stale-environment-data');
```

**Re-enable:**
```sql
-- Re-run the SELECT cron.schedule(...) statements from migrations 007 or 008
```

**Force immediate cleanup (manual trigger):**
```sql
DELETE FROM wearable_vitals WHERE recorded_at < NOW() - INTERVAL '30 days';
DELETE FROM environmental_data WHERE recorded_at < NOW() - INTERVAL '3 days';
```

## Why Different Retention Periods?

### Wearable Vitals: 30 Days
- **Reason**: Offline users need buffer for device sync when they return online
- **Use case**: AI generates weekly summaries from raw data
- **Value**: Raw minute-by-minute data loses 99% clinical value after summarization
- **Safety**: AI summaries become permanent medical record

### Environmental Data: 3 Days
- **Reason**: Weather/AQI cache to prevent Open-Meteo API rate-limiting
- **Use case**: On-demand fetching for current health advice
- **Value**: Weather data older than 3 days is outdated and irrelevant
- **Safety**: Long-term environmental context (if clinically relevant) is captured in AI summaries/alerts

## Clinical Safety

Raw data deletion is **clinically safe** because:
- AI-generated summaries (stored separately) preserve long-term patient narratives
- 30-day buffer accommodates device sync delays and offline users
- Summaries capture clinically significant trends that matter for long-term care
- Minute-by-minute raw data loses 99% of value after weekly aggregation

---

# Weekly AI Health Summaries

## What it does

The weekly AI health summary pipeline generates, stores, and retrieves personalized health summaries for patients. Two distinct summaries are produced per patient per run:

- **User-facing** (`target_role='user'`): A plain-language, empathetic 3-bullet wellbeing summary written for the patient.
- **Doctor-facing** (`target_role='doctor'`): A concise clinical summary written for the assigned physician, citing lab values and wearable anomalies with full reference ranges.

Summaries are produced by calling the Gemini LLM twice — one call per role — with the same 7-day wearable vitals and lab snapshot data as context.  A cron script fans out generation across all active patients asynchronously.

---

## Architecture

```
cron_weekly_summarizer.py
    │
    ├─ fetch active patient IDs from Supabase (role='patient', is_active=true)
    │
    └─ asyncio.Semaphore(10): for each patient, POST /api/v1/summaries/generate/{user_id}
            │
            └─ SummaryGenerator.generate_weekly_summaries(user_id)
                    │
                    ├─ 1. Data gathering
                    │       ├─ fetch_wearable_vitals(user_id, days=7)
                    │       └─ fetch_user_lab_snapshot(user_id)
                    │
                    ├─ 2. LLM generation (×2)
                    │       ├─ load_system_prompt("summary_user")   → system_summarizer_user.txt
                    │       ├─ load_system_prompt("summary_doctor") → system_summarizer_doctor.txt
                    │       └─ GeminiService.generate() × 2 (same data, different system prompts)
                    │
                    └─ 3. Storage
                            └─ INSERT INTO health_summaries (target_role='user' + 'doctor')


GET /api/v1/summaries/{target_user_id}?role=user&limit=4
    │
    ├─ get_current_user_with_role()   ← validates JWT + fetches role from users table
    │
    ├─ AuthZ: Patient → must be own user_id, role forced to 'user'
    │         Doctor  → must exist in doctor_patient_mapping
    │
    └─ SELECT FROM health_summaries ORDER BY created_at DESC LIMIT ?limit
```

---

## Database Schema (Migration 011)

```sql
CREATE TABLE health_summaries (
    id              UUID            PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID            NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    period_type     TEXT            NOT NULL DEFAULT 'weekly',
    target_role     TEXT            NOT NULL CHECK (target_role IN ('user', 'doctor')),
    summary_content TEXT            NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Efficient lookup: most recent summaries for a user + role
CREATE INDEX idx_health_summaries_user_role_created
    ON health_summaries (user_id, target_role, created_at DESC);
```

**Retention:** A `pg_cron` job (`purge-stale-health-summaries`) runs every Sunday at 05:00 UTC and deletes summaries older than 1 year.

**RLS Policies:**
- Patients can SELECT their own `target_role='user'` summaries.
- Doctors can SELECT `target_role='doctor'` summaries for patients in `doctor_patient_mapping`.

**Run:** Paste `src/db/migrations/011_add_health_summaries.sql` into the Supabase SQL editor.

---

## Prompt Registry Update

`src/backend/services/llm/prompt_builder.py` — two new entries added to each registry dict:

```python
_PROMPT_FILES = {
    ...
    "summary_user":   "system_summarizer_user.txt",   # NEW
    "summary_doctor": "system_summarizer_doctor.txt",  # NEW
}

_CITATION_FILES = {
    ...
    "summary_user":   "citation_summarizer.txt",  # NEW
    "summary_doctor": "citation_summarizer.txt",  # NEW
}
```

The generator service calls `load_system_prompt("summary_user")` etc. — it never reads prompt files from disk directly.  The existing prompt files (`system_summarizer_user.txt`, `system_summarizer_doctor.txt`, `citation_summarizer.txt`) were already present; only the registry entries were missing.

---

## Files Created / Modified

| File | Change |
|------|--------|
| `src/db/migrations/011_add_health_summaries.sql` | **New** — `health_summaries` table, composite index, pg_cron retention, RLS policies |
| `src/backend/services/llm/prompt_builder.py` | **Modified** — Added `summary_user` and `summary_doctor` to `_PROMPT_FILES` and `_CITATION_FILES` |
| `src/backend/services/summaries/__init__.py` | **New** — Package init, exports `SummaryGenerator` |
| `src/backend/services/summaries/generator.py` | **New** — `SummaryGenerator` class: data gathering → dual Gemini generation → Supabase persistence |
| `src/backend/middleware/auth_middleware.py` | **Modified** — Added `get_current_user_with_role()` (returns `{id, role}`) and `verify_service_role()` (validates service-role key) alongside unchanged `get_current_user()` |
| `src/backend/routes/summaries.py` | **New** — `POST /api/v1/summaries/generate/{user_id}` (service-role) and `GET /api/v1/summaries/{user_id}` (JWT + role-based AuthZ) |
| `src/backend/main.py` | **Modified** — Mounts the summaries router |
| `src/backend/scripts/cron_weekly_summarizer.py` | **New** — Async cron script with `asyncio.Semaphore(10)`, patients-only query, per-user error logging |

---

## API Endpoints

### POST /api/v1/summaries/generate/{target_user_id}

Trigger generation for a single patient.  **Service-role only** — called by cron.

**Auth:** `Authorization: Bearer <SUPABASE_SERVICE_ROLE_KEY>`

**Response (201):**
```json
{
  "status": "ok",
  "user_id": "<uuid>",
  "generated": ["user", "doctor"],
  "errors": []
}
```

---

### GET /api/v1/summaries/{target_user_id}

Retrieve stored summaries.  **JWT required.**

**Query parameters:**
- `role` — `'user'` or `'doctor'` (patients are auto-forced to `'user'`)
- `limit` — number of summaries to return (default `4`, max `10`)

**Response (200):**
```json
{
  "user_id": "<uuid>",
  "role": "user",
  "count": 4,
  "summaries": [
    {
      "id": "<uuid>",
      "user_id": "<uuid>",
      "period_type": "weekly",
      "target_role": "user",
      "summary_content": "- **Great momentum...** ...\n- **A quick note...**\n- **Your Weekly Goal...**",
      "created_at": "2026-04-04T00:00:00Z"
    }
  ]
}
```

**Authorization logic:**

| Requester role | target_user_id | `role` param | Result |
|---|---|---|---|
| `patient` | own ID | any | Forced to `role=user`, returns own summaries |
| `patient` | other ID | any | 403 |
| `doctor` | mapped patient | `user` or `doctor` | Returns requested role |
| `doctor` | unmapped patient | any | 403 |

---

## Cron Script

```bash
# Run manually (ensure .env is sourced or env vars exported)
cd src && python -m backend.scripts.cron_weekly_summarizer

# Environment variables required:
#   API_BASE_URL           — default: http://localhost:8000
#   SUPABASE_URL           — Supabase project URL
#   SUPABASE_SERVICE_ROLE_KEY — used to both query users table and authenticate the API call
```

The script:
1. Fetches all `users WHERE is_active = true AND role = 'patient'` from Supabase.
2. Fires one `POST /api/v1/summaries/generate/{user_id}` per patient in parallel, capped at 10 concurrent requests.
3. Logs failures per user and exits with code `1` if any user failed (useful for scheduler alerting).

---

## Auth Middleware Update

`src/backend/middleware/auth_middleware.py` now exports three dependency functions:

| Function | Returns | Purpose |
|---|---|---|
| `get_current_user()` | `str` (user_id) | Unchanged — used by existing routes |
| `get_current_user_with_role()` | `{"id": str, "role": str}` | Used by GET summaries for role-based AuthZ |
| `verify_service_role()` | `bool` | Used by POST generate and POST admin evaluate — validates service-role key |

No existing routes were broken — `get_current_user` is fully backward-compatible.

---

# Nightly Rules Sweep (Cron Automation — Week 6)

## What it does

The nightly rules sweep is a background cron job that automatically evaluates Person 1's 13-rule deterministic rules engine for **every active patient** every night.  It replaces stale alert data with fresh evaluations, ensuring the `alerts` and `alert_evidence` tables are always up-to-date when a patient or doctor opens the app in the morning.

Key characteristics:

- **Fully automated** — no user action required; external scheduler triggers the script nightly.
- **Idempotent** — safe to re-run; the rules engine deletes old alerts before inserting new ones.
- **Concurrent & non-blocking** — uses `asyncio` + `httpx.AsyncClient` with `Semaphore(10)` for bounded parallelism.
- **Fault-tolerant** — individual user failures are logged and do not block other evaluations.

---

## Architecture

```
cron_nightly_alerts.py
    │
    ├─ fetch active patient IDs from Supabase (role='patient', is_active=true)
    │
    └─ asyncio.Semaphore(10): for each patient, POST /alerts/admin/evaluate/{user_id}
            │
            └─ _run_evaluation(user_id)
                    │
                    ├─ evaluate_rules()   ← 13-rule deterministic rules engine
                    │       ├─ Fetch medical_reports + lab_results
                    │       ├─ Build LabRow objects
                    │       ├─ Run all 13 rules
                    │       └─ Apply environmental modifiers (AQI, temperature)
                    │
                    └─ persist_alerts()   ← idempotent store
                            ├─ DELETE old alerts for user
                            ├─ INSERT new alerts
                            └─ INSERT alert_evidence rows
```

---

## Endpoint Secured for Cron Access

A new **`POST /alerts/admin/evaluate/{user_id}`** endpoint was added alongside the existing user-facing `POST /alerts/evaluate/{user_id}`:

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /alerts/evaluate/{user_id}` | JWT (`get_current_user`) | User triggers own evaluation (existing) |
| `POST /alerts/admin/evaluate/{user_id}` | Service-role (`verify_service_role`) | Cron triggers evaluation for any patient (**new**) |

Both endpoints delegate to the same `_run_evaluation()` helper function (DRY principle).

**Response (200):**
```json
{
  "user_id": "<uuid>",
  "alerts_triggered": 4,
  "deleted": 3,
  "inserted": 4,
  "evidence_inserted": 8,
  "errors": []
}
```

---

## Cron Script

```bash
# Run manually (ensure .env is sourced or env vars exported)
cd src && python -m backend.scripts.cron_nightly_alerts

# Environment variables required:
#   API_BASE_URL                — default: http://localhost:8000
#   SUPABASE_URL                — Supabase project URL
#   SUPABASE_SERVICE_ROLE_KEY   — used to both query users table and authenticate the API call
```

The script:
1. Fetches all `users WHERE is_active = true AND role = 'patient'` from Supabase.
2. Fires one `POST /alerts/admin/evaluate/{user_id}` per patient in parallel, capped at 10 concurrent requests.
3. Logs successes and failures per user with a final summary report.
4. Exits with code `1` if any user failed (useful for scheduler alerting).

### Example output

```
2026-04-05 02:00:01  INFO      cron_nightly_alerts  Starting nightly rules-engine sweep.
2026-04-05 02:00:01  INFO      cron_nightly_alerts  API_BASE_URL = http://localhost:8000
2026-04-05 02:00:02  INFO      cron_nightly_alerts  Found 47 active patients to evaluate.
2026-04-05 02:00:38  INFO      cron_nightly_alerts  Nightly sweep complete in 36.2s: 46 succeeded, 1 failed out of 47 total.
2026-04-05 02:00:38  INFO      cron_nightly_alerts    OK   user_id=abc123: alerts_triggered=3, inserted=3
2026-04-05 02:00:38  ERROR     cron_nightly_alerts  FAILED user_id=def456: Request timed out
```

---

## SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **Single Responsibility** | `_run_evaluation()` handles rules-engine orchestration only. Auth checking is handled by FastAPI dependencies. The cron script handles user discovery and HTTP fan-out only. |
| **Open/Closed** | Adding the admin endpoint did NOT modify the existing user-facing endpoint's logic — it added a new route alongside it. The `_run_evaluation` helper is shared by composition, not inheritance. |
| **Liskov Substitution** | Both `verify_service_role` and `get_current_user` satisfy the same FastAPI dependency injection interface (`Depends()`). Either can be used interchangeably in a route signature. |
| **Interface Segregation** | The cron script depends only on httpx + Supabase client. It does not import the rules engine, FastAPI, or any internal services. It interacts with the backend exclusively through the HTTP API boundary. |
| **Dependency Inversion** | The cron script depends on the abstract HTTP API contract (`POST /alerts/admin/evaluate/{user_id}`), not on concrete internal classes. The rules engine implementation can change without touching the cron script. |

---

## Files Created / Modified

| File | Change |
|------|--------|
| `src/backend/routes/alerts.py` | **Modified** — Added `POST /alerts/admin/evaluate/{user_id}` endpoint with `verify_service_role` dependency. Extracted shared `_run_evaluation()` helper (DRY refactor). Existing user-facing endpoint unchanged in behaviour. |
| `src/backend/scripts/cron_nightly_alerts.py` | **New** — Async cron script with `asyncio.Semaphore(10)`, 60s timeout, per-user error logging, and non-zero exit on failures. |

---

## Configuration

All configuration is via environment variables (same as `cron_weekly_summarizer.py`):

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `API_BASE_URL` | No | `http://localhost:8000` | FastAPI backend URL |
| `SUPABASE_URL` | Yes | — | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | — | Service-role key for both DB queries and API auth |

---

## Scheduler Integration (Production)

The cron script is designed to be triggered by any external scheduler:

```bash
# Linux cron (run at 2:00 AM daily)
0 2 * * *  cd /path/to/src && python -m backend.scripts.cron_nightly_alerts >> /var/log/nightly_alerts.log 2>&1

# Cloud Scheduler / Kubernetes CronJob / GitHub Actions — similar approach
```

---