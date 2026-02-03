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

