"""Pytest configuration and shared fixtures for integration tests."""
import os
import sys
import uuid
from pathlib import Path
from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Add src/backend to path so we can import backend modules
backend_dir = Path(__file__).resolve().parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_dir.parent))

# Load environment variables before importing the app
env_file = backend_dir / ".env"
load_dotenv(env_file, override=False)

from backend.main import app
from backend.config.supabase_client import get_supabase_client


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """Create a FastAPI test client for the entire test session."""
    return TestClient(app)


@pytest.fixture(scope="session")
def supabase_client():
    """Create a Supabase client for direct database operations."""
    return get_supabase_client()


@pytest.fixture(scope="function")
def test_user_id() -> str:
    """Generate a unique test user ID for each test.

    This ensures test isolation - each test gets its own user.
    """
    return str(uuid.uuid4())


@pytest.fixture(scope="session")
def sample_pdf_path() -> Path:
    """Path to a sample PDF for testing uploads."""
    pdf_path = Path(__file__).resolve().parent.parent / "src" / "frontend" / "public" / "full_body_checkup.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF not found at {pdf_path}")
    return pdf_path


@pytest.fixture(scope="function")
def test_user(test_client: TestClient, test_user_id: str) -> dict:
    """Create a test user in the database and return user data.

    This fixture automatically creates a user before the test runs.
    The user is NOT automatically deleted after the test to allow
    inspection of test data in the database.
    """
    user_data = {
        "email": f"test_{test_user_id[:8]}@example.com",
        "full_name": "Test User",
        "phone": "+919876543210",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "blood_group": "O+",
        "height_cm": 175,
        "weight_kg": 70
    }

    response = test_client.post("/api/v1/users", json=user_data)
    if response.status_code != 201:
        pytest.fail(f"Failed to create test user: {response.text}")

    created_user = response.json()
    return created_user


@pytest.fixture(scope="function")
def uploaded_report(
    test_client: TestClient,
    test_user: dict,
    sample_pdf_path: Path
) -> dict:
    """Upload a test PDF and return the report metadata.

    This fixture creates a user, uploads a PDF, and waits for processing.
    Useful for tests that need a fully processed report.
    """
    user_id = test_user["id"]

    with open(sample_pdf_path, "rb") as f:
        files = {"file": ("test_report.pdf", f, "application/pdf")}
        data = {"user_id": user_id, "user_name": test_user["full_name"]}
        response = test_client.post("/reports/ingest", files=files, data=data)

    if response.status_code != 202:
        pytest.fail(f"Failed to upload test PDF: {response.text}")

    return response.json()


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (may be slow)"
    )
    config.addinivalue_line(
        "markers", "requires_env: mark test as requiring environment variables"
    )
    config.addinivalue_line(
        "markers", "requires_pdf: mark test as requiring sample PDF file"
    )
