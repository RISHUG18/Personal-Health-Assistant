# Integration Tests

Comprehensive integration tests for the Personal Health Assistant API.

## Overview

These tests simulate real user behavior and validate that all system components work together correctly:

- **User Operations** (`test_user_operations.py`): User CRUD operations
- **PDF Upload** (`test_pdf_upload.py`): Medical report upload and processing
- **RAG Query** (`test_rag_query.py`): AI-powered health queries and suggestions
- **Rules Engine** (`test_alerts_rules.py`): Deterministic alert generation
- **End-to-End** (`test_end_to_end.py`): Complete user journey simulation

## Prerequisites

### 1. Install Dependencies

```bash
cd src/backend
pip install -r requirements.txt
pip install pytest pytest-asyncio
```

### 2. Environment Variables

Ensure your `.env` file is properly configured in `src/backend/.env`:

```bash
# Required for tests
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-pro-preview

# Optional
SUPABASE_BUCKET_NAME=medical-reports
SUPABASE_REPORTS_TABLE=medical_reports
```

### 3. Database Setup

Run all migrations before testing:

```bash
# Ensure migrations 000-005 are applied to your Supabase database
```

### 4. Sample PDF

Tests use `src/frontend/public/full_body_checkup.pdf` as sample data. Ensure this file exists.

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/ -v

# Or from src/backend
pytest ../../tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_user_operations.py -v
pytest tests/test_pdf_upload.py -v
pytest tests/test_rag_query.py -v
pytest tests/test_alerts_rules.py -v
pytest tests/test_end_to_end.py -v
```

### Run Specific Test Class or Method

```bash
# Run a specific test class
pytest tests/test_user_operations.py::TestUserOperations -v

# Run a specific test method
pytest tests/test_end_to_end.py::TestEndToEndUserJourney::test_complete_user_journey -v
```

### Run Tests by Marker

```bash
# Run only integration tests
pytest tests/ -m integration -v

# Run tests that require PDF
pytest tests/ -m requires_pdf -v

# Skip tests that require environment variables
pytest tests/ -m "not requires_env" -v
```

## Test Structure

### Fixtures (conftest.py)

- `test_client`: FastAPI test client (session scope)
- `supabase_client`: Supabase client for direct DB operations
- `test_user_id`: Unique UUID for each test (function scope)
- `test_user`: Pre-created test user (function scope)
- `uploaded_report`: Pre-uploaded and processed PDF report (function scope)
- `sample_pdf_path`: Path to sample PDF file

### Test Coverage

#### User Operations (15 tests)
- Create user with valid/invalid data
- Get user by ID/email
- Update user profile
- Delete user
- Handle duplicate emails
- Validation for blood group, email, etc.

#### PDF Upload (8 tests)
- Basic upload to storage
- Async ingestion pipeline (recommended)
- Sync processing (blocking)
- Status polling
- Lab results extraction
- Error handling for invalid inputs

#### RAG Query (12 tests)
- Basic query without grounding
- Query with processed reports (grounded)
- Empty/whitespace query validation
- Doctor vs user role
- Section filtering (Week 4)
- Environmental data integration
- GPS coordinates
- FAISS vs pgvector retrieval
- Similarity threshold tuning

#### Rules Engine & Alerts (9 tests)
- Evaluate rules with/without reports
- Alert generation and persistence
- Alert retrieval with/without evidence
- Idempotency of rule evaluation
- Severity level validation
- Invalid user handling

#### End-to-End (2 comprehensive tests)
- Complete user journey: signup → upload → process → query → alerts → update
- Environment-aware query journey

## Expected Behavior

### Test Data Isolation

Each test uses a unique `test_user_id` to ensure isolation. Tests do NOT automatically clean up data after execution, allowing you to inspect results in the database.

### Timing

- **Fast tests** (user CRUD): < 1 second
- **Medium tests** (PDF upload): 30-60 seconds (OCR + Gemini)
- **Comprehensive E2E**: 90-120 seconds

### Assertions

Tests verify:
- Correct HTTP status codes
- Response structure and data types
- Business logic (e.g., duplicate email rejected)
- Data persistence in database
- Gemini model version (must be `gemini-3.1-pro-preview`)
- Alert severity levels (low/medium/high/critical)

## Troubleshooting

### Tests Fail with "Connection Refused"

**Problem**: FastAPI server not accessible.

**Solution**: Tests use `TestClient` which doesn't require a running server. Ensure imports are correct.

### Tests Fail with "GEMINI_API_KEY not found"

**Problem**: Missing API key in environment.

**Solution**:
```bash
export GEMINI_API_KEY=your_key
# Or add to src/backend/.env
```

### Tests Timeout During PDF Processing

**Problem**: Gemini API is slow or rate-limited.

**Solution**:
- Increase `max_wait` in affected tests
- Check Gemini API quota
- Use `pytest -k "not pdf"` to skip PDF tests temporarily

### Tests Leave Data in Database

**Behavior**: This is intentional for debugging.

**Cleanup**: Manually delete test users via Supabase dashboard or SQL:
```sql
DELETE FROM users WHERE email LIKE 'test_%@%' OR email LIKE '%_test_%@%';
```

### FileNotFoundError: sample PDF

**Problem**: `src/frontend/public/full_body_checkup.pdf` not found.

**Solution**:
- Ensure the file exists at that path
- Or update `sample_pdf_path` fixture in `conftest.py`

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd src/backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run tests
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          pytest tests/ -v --tb=short
```

## Extending Tests

### Adding New Tests

1. Create new test file: `tests/test_feature.py`
2. Import fixtures from `conftest.py`
3. Use appropriate markers (`@pytest.mark.integration`, etc.)
4. Follow naming convention: `test_*` for functions, `Test*` for classes

### Custom Fixtures

Add to `conftest.py`:

```python
@pytest.fixture
def custom_fixture(test_client):
    # Setup
    resource = create_resource()
    yield resource
    # Teardown (optional)
    cleanup_resource(resource)
```

## Best Practices

1. **Use descriptive test names**: `test_create_user_with_duplicate_email_fails`
2. **Print progress**: Use `print()` for visibility during long-running tests
3. **Fail early**: Assert critical conditions before proceeding
4. **Skip gracefully**: Use `pytest.skip()` for expected failures (API timeouts)
5. **Test real scenarios**: Mimic actual user behavior, not just technical operations

## Test Results Interpretation

### All tests pass ✓

System is working correctly end-to-end.

### PDF tests fail

Check Gemini API key, rate limits, or network connectivity.

### RAG query tests fail

Verify embedding model is loaded, pgvector extension is enabled in Supabase.

### User tests fail

Check database migrations, foreign key constraints, and Supabase permissions.

### Alerts tests fail

Verify rules engine code is present in `src/backend/rules/` and importable.

## Performance Benchmark

On a typical setup:

```
test_user_operations.py .......... 2.3s
test_pdf_upload.py ........ 45.6s
test_rag_query.py ............ 18.2s
test_alerts_rules.py ......... 52.1s
test_end_to_end.py .. 95.4s

Total: ~214s for 45+ tests
```

## Contact

For issues with tests, check:
1. This README
2. Test docstrings
3. `conftest.py` fixture documentation
4. Main project documentation in `src/README1.md`
