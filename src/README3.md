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

# Context Object Schema (Gemini)

## Functionalities
- Defines the context payload structure sent to Gemini
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
3) Payload is validated against the schema before Gemini call.

