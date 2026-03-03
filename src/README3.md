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

# Query Embedding (New Work)

## What it does

The query embedding module converts a user query (and/or document chunks) into dense vectors.
These vectors are intended to be used by the retrieval layer (FAISS/pgvector) for similarity search.

This work was implemented with SOLID principles in mind:
- **DIP (Dependency Inversion Principle):** the rest of the code depends on an `Embedder` interface, not a specific model.
- **OCP (Open/Closed Principle):** adding a new embedding provider is done by creating a new implementation without changing call sites.

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
	- `build_context(query, user_id, retrieved_chunks, ...)` — pure assembly function; validates all inputs via Pydantic; applies size controls (max 5 chunks, 500 chars/chunk, 4000 chars total).

- [src/backend/services/context/data_fetchers.py](src/backend/services/context/data_fetchers.py)
	- `fetch_active_alerts(user_id)` — queries the `alerts` table for open alerts.
	- `fetch_user_lab_snapshot(user_id)` — queries `lab_results` (joined to `medical_reports`) and maps known test names to the `recent_vitals` block.
	- `fetch_user_profile(user_id)` — stub for user demographics; returns empty dict until a `user_profiles` table is created.
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
                ├─ trim chunks: max 5, max 500 chars each, max 4000 chars total
                ├─ normalise alert keys (reason ↔ message, severity lowercase)
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

