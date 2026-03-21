# User Schema Migration Guide

This guide explains how to set up the users table and apply the necessary database migrations.

## Overview

The user schema provides a comprehensive user profile system with:
- Basic user information (name, email, phone)
- Address details
- Medical information (blood group, height, weight)
- Account metadata (created_at, updated_at, last_login_at, is_active)

## Database Migrations

### Order of Migration Application

**IMPORTANT**: Migrations must be applied in the following order:

1. **000_create_users_table.sql** (NEW - Apply this FIRST)
2. **001_add_report_chunks.sql**
3. **002_add_report_chunk_metadata.sql**
4. **003_add_chunk_section_metadata.sql**
5. **003_add_processing_status.sql**
6. **004_add_section_filter_to_rpc.sql**
7. **005_add_environmental_data.sql** (UPDATED to reference users table)

### Applying Migrations in Supabase

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Navigate to your project
3. Click on **SQL Editor** in the left sidebar
4. For each migration file (in order):
   - Open the file: `src/db/migrations/XXX_migration_name.sql`
   - Copy the entire contents
   - Paste into the SQL Editor
   - Click **Run** or press `Ctrl+Enter`
   - Verify success (check for errors in the output)

### Migration 000: Create Users Table

```sql
-- This creates the core users table that will be referenced by:
-- - medical_reports.user_id
-- - alerts.user_id
-- - environmental_data.user_id

CREATE TABLE IF NOT EXISTS users (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT        UNIQUE NOT NULL,
    full_name       TEXT        NOT NULL,
    phone           TEXT,
    date_of_birth   DATE,
    gender          TEXT        CHECK (gender IN ('male', 'female', 'other')),

    -- Address information
    address_line1   TEXT,
    address_line2   TEXT,
    city            TEXT,
    state           TEXT,
    postal_code     TEXT,
    country         TEXT        DEFAULT 'India',

    -- Medical information
    blood_group     TEXT        CHECK (blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    height_cm       NUMERIC,
    weight_kg       NUMERIC,

    -- Account metadata
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at   TIMESTAMP WITH TIME ZONE,
    is_active       BOOLEAN     DEFAULT TRUE
);
```

### Migration 005: Environmental Data (Updated)

The foreign key has been updated from `auth.users(id)` to `users(id)`:

```sql
-- OLD (incorrect):
user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

-- NEW (correct):
user_id UUID REFERENCES users(id) ON DELETE CASCADE,
```

## API Endpoints

Once migrations are applied, the following user management endpoints will be available:

### Create User
```http
POST /api/v1/users
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+91-9876543210",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India",
  "blood_group": "O+",
  "height_cm": 175.0,
  "weight_kg": 70.0
}
```

### Get User by ID
```http
GET /api/v1/users/{user_id}
```

### Get User by Email
```http
GET /api/v1/users/email/{email}
```

### Update User
```http
PATCH /api/v1/users/{user_id}
Content-Type: application/json

{
  "phone": "+91-9876543211",
  "weight_kg": 72.0
}
```

### Delete User
```http
DELETE /api/v1/users/{user_id}
```

**Note**: Deleting a user will cascade delete all related data:
- Medical reports
- Lab results
- Alerts
- Environmental data

## Using the User Schema in Code

### Import the Models

```python
from backend.models.user import User, UserCreate, UserUpdate, UserResponse
```

### Create a New User

```python
from backend.controllers.users_controller import create_user
from backend.models.user import UserCreate

user_data = UserCreate(
    email="test@example.com",
    full_name="Test User",
    phone="+91-1234567890",
    city="Delhi",
    blood_group="A+"
)

user = create_user(user_data)
print(f"Created user with ID: {user.id}")
```

### Get User by ID

```python
from backend.controllers.users_controller import get_user_by_id

user = get_user_by_id("aaaaaaaa-0001-0001-0001-000000000001")
print(f"User: {user.full_name} ({user.email})")
```

### Update User

```python
from backend.controllers.users_controller import update_user
from backend.models.user import UserUpdate

update_data = UserUpdate(
    phone="+91-9999999999",
    weight_kg=75.0
)

updated_user = update_user(user_id, update_data)
```

## Gemini Model Configuration

All Gemini API calls now use **gemini-3.1-pro-preview** as the default model.

### Configuration Files Updated:
1. **src/backend/services/llm/gemini_service.py** - Main LLM service
2. **src/backend/services/preprocessing/gemini_cleaning.py** - OCR text cleaning
3. **src/backend/extraction/gemini_extractor.py** - Lab data extraction
4. **src/backend/routes/rag.py** - RAG query pipeline

### Environment Variable

The model is configured via the `.env` file:

```bash
GEMINI_MODEL="gemini-3.1-pro-preview"
```

All code now respects this environment variable with the correct fallback:

```python
model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
```

## Verification

After applying migrations, verify the setup:

1. **Check tables exist**:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('users', 'medical_reports', 'alerts', 'environmental_data');
```

2. **Check foreign keys**:
```sql
SELECT conname, conrelid::regclass AS table_name,
       confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE contype = 'f'
  AND confrelid::regclass::text = 'users';
```

Expected output should show:
- `medical_reports.user_id` → `users.id`
- `alerts.user_id` → `users.id`
- `environmental_data.user_id` → `users.id`

3. **Test user creation**:
```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "Test User"
  }'
```

## Troubleshooting

### Foreign Key Constraint Errors

If you see errors like:
```
ERROR: insert or update on table "environmental_data" violates foreign key constraint
DETAIL: Key (user_id)=(xxx) is not present in table "users".
```

**Solution**: Run migration `000_create_users_table.sql` first, then re-run the failing migration.

### Migration Already Applied

If you see:
```
ERROR: relation "users" already exists
```

This is safe to ignore if the table was already created. The migrations use `CREATE TABLE IF NOT EXISTS`.

### Model Not Found Errors

If you see:
```
The model `gemini-2.0-flash` does not exist
```

**Solution**: Update to the latest code which uses `gemini-3.1-pro-preview` throughout.

## Summary of Changes

1. ✅ Created `000_create_users_table.sql` migration
2. ✅ Updated `schema.sql` to include users table with foreign keys
3. ✅ Fixed `005_add_environmental_data.sql` foreign key reference
4. ✅ Created user models in `backend/models/user.py`
5. ✅ Created user controller in `backend/controllers/users_controller.py`
6. ✅ Created user routes in `backend/routes/users.py`
7. ✅ Registered user routes in `backend/main.py`
8. ✅ Updated all Gemini model defaults to `gemini-3.1-pro-preview`
