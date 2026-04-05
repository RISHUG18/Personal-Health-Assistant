#!/usr/bin/env python3
"""Async cron script — nightly rules-engine sweep for all active patients.

Architecture
------------
This script is designed to be invoked by an external scheduler (cron, Cloud
Scheduler, Kubernetes CronJob, etc.) once per night.  It does NOT loop forever.

It mirrors the scalable ``asyncio`` + ``httpx.AsyncClient`` pattern
established by ``cron_weekly_summarizer.py``.

What it does
------------
For every active patient, the script POSTs to the service-role-protected
``/alerts/admin/evaluate/{user_id}`` endpoint.  That endpoint runs Person 1's
13-rule deterministic rules engine, persists any triggered alerts into the
``alerts`` + ``alert_evidence`` tables, and returns a summary of what was
stored.

Scalability
-----------
* Uses ``asyncio`` + ``httpx.AsyncClient`` — all HTTP calls are non-blocking.
* ``asyncio.Semaphore(10)`` limits concurrent requests to the backend to stay
  within database connection limits and avoid overloading the FastAPI server.
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
    the ``POST /alerts/admin/evaluate/{user_id}`` endpoint accepts the request.

Usage
-----
::

    # Run directly (ensure .env is sourced or vars are exported)
    python -m backend.scripts.cron_nightly_alerts

    # Or from the repo root:
    cd src && python -m backend.scripts.cron_nightly_alerts
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

# ── Bootstrap env (same pattern as main.py / cron_weekly_summarizer) ──────────
_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_FILE, override=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("cron_nightly_alerts")

# ── Configuration ─────────────────────────────────────────────────────────────

API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Maximum concurrent requests to the backend (protects DB connection pool).
MAX_CONCURRENCY: int = 10

# Per-request timeout (seconds).  Rules evaluation touches multiple tables
# and can be slow on large data sets.
REQUEST_TIMEOUT: float = 60.0


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


async def _evaluate_for_user(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    user_id: str,
) -> tuple[str, bool, str]:
    """POST to the admin evaluate endpoint for a single user.

    Returns
    -------
    tuple[str, bool, str]
        ``(user_id, success, detail_message)``
    """
    url = f"{API_BASE_URL.rstrip('/')}/alerts/admin/evaluate/{user_id}"

    async with semaphore:
        try:
            resp = await client.post(url, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (200, 201):
                body = resp.json()
                return (
                    user_id,
                    True,
                    f"alerts_triggered={body.get('alerts_triggered', 0)}, "
                    f"inserted={body.get('inserted', 0)}",
                )
            else:
                return (user_id, False, f"HTTP {resp.status_code}: {resp.text[:200]}")
        except httpx.TimeoutException:
            return (user_id, False, "Request timed out")
        except Exception as exc:
            return (user_id, False, str(exc))


# ── Main ──────────────────────────────────────────────────────────────────────

async def _run() -> None:
    """Core async logic: query users → fan-out evaluation requests → report."""
    logger.info("Starting nightly rules-engine sweep.")
    logger.info("API_BASE_URL = %s", API_BASE_URL)

    # ── 1. Fetch all active patients ──────────────────────────────────────────
    user_ids = _fetch_active_patient_ids()
    logger.info("Found %d active patients to evaluate.", len(user_ids))

    if not user_ids:
        logger.info("No patients to process — exiting.")
        return

    # ── 2. Fan-out with bounded concurrency ───────────────────────────────────
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}

    t0 = time.monotonic()

    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [
            _evaluate_for_user(client, semaphore, uid) for uid in user_ids
        ]
        results = await asyncio.gather(*tasks)

    elapsed = time.monotonic() - t0

    # ── 3. Summary report ─────────────────────────────────────────────────────
    succeeded = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    logger.info(
        "Nightly sweep complete in %.1fs: %d succeeded, %d failed out of %d total.",
        elapsed,
        len(succeeded),
        len(failed),
        len(results),
    )

    for uid, _, detail in succeeded:
        logger.info("  OK   user_id=%s: %s", uid, detail)

    for uid, _, detail in failed:
        logger.error("FAILED user_id=%s: %s", uid, detail)

    if failed:
        # Exit with non-zero so external schedulers can alert on failure.
        sys.exit(1)


def main() -> None:
    """Entry point for ``python -m backend.scripts.cron_nightly_alerts``."""
    if not SUPABASE_SERVICE_KEY:
        logger.error(
            "SUPABASE_SERVICE_ROLE_KEY is not set.  "
            "The cron script cannot authenticate with the API."
        )
        sys.exit(1)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
