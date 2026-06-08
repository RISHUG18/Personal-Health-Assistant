"""Celery application configuration for report processing workers.

Usage
-----
Start a worker (from the ``src/backend`` directory or with PYTHONPATH set)::

    celery -A backend.worker.celery_app worker --loglevel=info --concurrency=4

With auto-scaling::

    celery -A backend.worker.celery_app worker --loglevel=info \\
        --autoscale=8,2

See ``start_worker.sh`` in the ``src/backend`` directory for a convenience
wrapper that sets the correct environment.

Worker lifecycle logging
------------------------
Three signals emit structured log lines so you can see exactly how many
worker threads come online:

  ``worker_init``    — fires once in the main worker process at launch.
  ``worker_ready``   — fires once when the pool is fully warmed up.
  ``worker_process_init`` — fires inside *each* pool subprocess/thread,
                            so you get one log line per concurrent slot.
"""
import logging
import os
from pathlib import Path

from celery import Celery
from celery.signals import worker_init, worker_ready, worker_process_init
from dotenv import load_dotenv

# Load .env from repo root so all env vars are available in worker processes.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_ENV_FILE, override=False)

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_log = logging.getLogger(__name__)

celery_app = Celery(
    "report_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.worker.tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Queue Routing
    task_default_queue="default",
    task_routes={
        "backend.worker.tasks.process_report": {"queue": "reports"},
        # Add future workers here, e.g.:
        # "backend.worker.tasks.send_email": {"queue": "mail"},
    },

    # Reliability: acknowledge only after task completes successfully
    task_acks_late=True,
    # Disable prefetch so each worker only picks up one task at a time —
    # critical for heavy OCR/Gemini jobs that may hold the GIL or saturate I/O.
    worker_prefetch_multiplier=1,

    # Track task start time in the result backend
    task_track_started=True,

    # Auto-retry configuration defaults (tasks can override per-task)
    task_soft_time_limit=300,   # 5 min soft limit — allows cleanup
    task_time_limit=360,        # 6 min hard kill

    # Result TTL — keep results in Redis for 1 hour
    result_expires=3600,

    # Timezone
    enable_utc=True,
)


# ── Worker lifecycle signals ──────────────────────────────────────────────────

@worker_init.connect
def on_worker_init(sender, **kwargs):
    """Fires once in the main worker process when it first starts up."""
    concurrency = os.getenv("CELERY_CONCURRENCY", "?")
    _log.info(
        "═══ Celery worker initialising ══════════════════════════\n"
        "  hostname    : %s\n"
        "  broker      : %s\n"
        "  concurrency : %s thread(s) will be spawned\n"
        "  pid         : %s\n"
        "═════════════════════════════════════════════════════════",
        getattr(sender, "hostname", "unknown"),
        REDIS_URL,
        concurrency,
        os.getpid(),
    )


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """Fires once when the worker pool is fully warmed up and ready to accept tasks."""
    pool = getattr(sender, "pool", None)
    num_processes = getattr(pool, "num_processes", None)
    _log.info(
        "✔ Celery worker READY — %s concurrent slot(s) accepting tasks  [pid=%s]",
        num_processes if num_processes is not None else os.getenv("CELERY_CONCURRENCY", "?"),
        os.getpid(),
    )


@worker_process_init.connect
def on_worker_process_init(sender, **kwargs):
    """Fires inside each worker pool subprocess/thread as it comes online.

    You will see this log line once per CELERY_CONCURRENCY value, confirming
    that exactly that many parallel execution slots are live.
    """
    _log.info(
        "  ↳ Worker pool slot online  [pid=%s]", os.getpid(),
    )
