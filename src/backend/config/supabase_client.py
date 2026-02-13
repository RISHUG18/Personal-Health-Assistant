"""Supabase client configuration and helpers."""
import os
from functools import lru_cache
from typing import Final

from dotenv import load_dotenv
from supabase import Client, create_client


class SupabaseConfigError(RuntimeError):
    """Raised when mandatory Supabase configuration is missing."""


# Environment variables that configure Supabase access.
SUPABASE_URL_ENV: Final[str] = "SUPABASE_URL"
SUPABASE_KEY_ENV: Final[str] = "SUPABASE_SERVICE_ROLE_KEY"
SUPABASE_BUCKET_ENV: Final[str] = "SUPABASE_REPORTS_BUCKET"
SUPABASE_OCR_TABLE_ENV: Final[str] = "SUPABASE_OCR_REPORTS_TABLE"

# Load .env once on module import so env vars are available for client creation.
load_dotenv()


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a singleton Supabase client configured from environment variables."""
    url = os.getenv(SUPABASE_URL_ENV)
    key = os.getenv(SUPABASE_KEY_ENV)
    if not url or not key:
        raise SupabaseConfigError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set for storage uploads."
        )
    # Create and cache the Supabase client for reuse across requests.
    return create_client(url, key)


def get_reports_bucket() -> str:
    """Return the target storage bucket for medical reports."""
    # Default bucket name keeps configuration optional for local development.
    return os.getenv(SUPABASE_BUCKET_ENV, "medical-reports")


def get_ocr_reports_table() -> str:
    """Return the table name for OCR report metadata."""
    return os.getenv(SUPABASE_OCR_TABLE_ENV, "medical_reports")


def fetch_ocr_text_by_report_id(report_id: str) -> str | None:
    """
    Fetch OCR text from Supabase database using report_id.
    Returns OCR text or None if not found.
    """
    client = get_supabase_client()
    table = get_ocr_reports_table()

    try:
        response = (
            client.table(table)
            .select("ocr_text")
            .eq("id", report_id)
            .limit(1)
            .execute()
        )

        data = response.data

        if not data:
            print("No OCR found for report:", report_id)
            return None

        return data[0].get("ocr_text")

    except Exception as e:
        print("Supabase fetch OCR error:", e)
        return None
