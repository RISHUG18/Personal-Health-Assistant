#!/usr/bin/env python3
"""Async cron script — weekly health summary generation for all active patients.

Architecture
------------
This script is designed to be invoked by an external scheduler (cron, Cloud
Scheduler, Kubernetes CronJob, etc.) once a week.  It does NOT loop forever.

Scalability
-----------
* Uses ``asyncio`` + ``httpx.AsyncClient`` — all HTTP calls are non-blocking.
* ``asyncio.Semaphore(10)`` limits concurrent requests to the backend to stay
  within the Gemini API rate limits.
* Each user is processed independently; a failure for one user does not block
  others.

Configuration (environment variables)
--------------------------------------
``API_BASE_URL``
    Base URL of the running FastAPI backend.
    Default: ``http://localhost:8000``

``SUPABASE_URL``
    Supabase project URL (for querying the user list).

``SUPABASE_SERVICE_ROLE_KEY``
    Service-role key injected into the ``Authorization: Bearer`` header so
    the ``POST /api/v1/summaries/generate/{user_id}`` endpoint accepts the
    request.

Usage
-----
::

    # Run directly (ensure .env is sourced or vars are exported)
    python -m backend.scripts.cron_weekly_summarizer

    # Or from the repo root:
    cd src && python -m backend.scripts.cron_weekly_summarizer
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

# ── Bootstrap env (same pattern as main.py) ───────────────────────────────────
_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_FILE, override=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("cron_weekly_summarizer")

# ── Configuration ─────────────────────────────────────────────────────────────

API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Maximum concurrent requests to the backend (protects Gemini rate limits).
MAX_CONCURRENCY: int = 10

# Per-request timeout (seconds).  Summary generation involves two Gemini
# calls so it can be slow.
REQUEST_TIMEOUT: float = 120.0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_active_patient_ids() -> list[str]:
    """Synchronously fetch all active patient IDs from Supabase.

    Uses the Supabase Python client (sync) because this is a one-shot script
    and the async client adds no benefit for a single DB query.
    """
    from supabase import create_client

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set.")
        sys.exit(1)

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    resp = (
        client.table("users")
        .select("id")
        .eq("is_active", True)
        .eq("role", "patient")
        .execute()
    )
    rows = resp.data or []
    return [row["id"] for row in rows if row.get("id")]


async def _generate_for_user(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    user_id: str,
) -> tuple[str, bool, str]:
    """POST to the generate endpoint for a single user.

    Returns
    -------
    tuple[str, bool, str]
        ``(user_id, success, detail_message)``
    """
    url = f"{API_BASE_URL.rstrip('/')}/api/v1/summaries/generate/{user_id}"

    async with semaphore:
        try:
            resp = await client.post(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (200, 201):
                body = resp.json()
                return (user_id, True, f"generated={body.get('generated', [])}")
            else:
                return (user_id, False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        except httpx.TimeoutException:
            return (user_id, False, "Request timed out")
        except Exception as exc:
            return (user_id, False, str(exc))


# ── Main ──────────────────────────────────────────────────────────────────────

async def _run() -> None:
    """Core async logic: query users → fan-out requests → report."""
    logger.info("Starting weekly summary generation cron job.")
    logger.info("API_BASE_URL = %s", API_BASE_URL)

    # ── 1. Fetch all active patients ──────────────────────────────────────────
    user_ids = _fetch_active_patient_ids()
    logger.info("Found %d active patients to process.", len(user_ids))

    if not user_ids:
        logger.info("No patients to process — exiting.")
        return

    # ── 2. Fan-out with bounded concurrency ───────────────────────────────────
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}

    t0 = time.monotonic()

    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [
            _generate_for_user(client, semaphore, uid) for uid in user_ids
        ]
        results = await asyncio.gather(*tasks)

    elapsed = time.monotonic() - t0

    # ── 3. Report ─────────────────────────────────────────────────────────────
    succeeded = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    logger.info(
        "Cron job complete in %.1fs: %d succeeded, %d failed out of %d total.",
        elapsed,
        len(succeeded),
        len(failed),
        len(results),
    )

    for uid, _, detail in failed:
        logger.error("FAILED user_id=%s: %s", uid, detail)

    if failed:
        # Exit with non-zero so external schedulers can alert on failure.
        sys.exit(1)


def main() -> None:
    """Entry point for ``python -m backend.scripts.cron_weekly_summarizer``."""
    if not SUPABASE_SERVICE_KEY:
        logger.error(
            "SUPABASE_SERVICE_ROLE_KEY is not set.  "
            "The cron script cannot authenticate with the API."
        )
        sys.exit(1)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
