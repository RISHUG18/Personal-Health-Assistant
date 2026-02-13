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

