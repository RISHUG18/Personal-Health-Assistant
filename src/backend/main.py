"""FastAPI application entrypoint."""
import asyncio
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root regardless of the working directory.
# This must run before any module that calls os.getenv() for Supabase/Gemini keys.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_ENV_FILE, override=False)  # override=False: shell env vars win

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import reports
from backend.routes import rag
from backend.routes import alerts
from backend.routes import users
from backend.routes import auth
from backend.routes import upload
from backend.routes import vitals
from backend.routes import environment
from backend.routes import voice
from backend.routes import summaries
from backend.routes import debug
from backend.routes import doctor
from backend.routes import report_status_ws
from backend.services.report_status_ws import report_status_connection_manager
from backend.services.retrieval.mock_retrieval import retrieve_mock_context

_log = logging.getLogger(__name__)


# ── Celery worker auto-start ──────────────────────────────────────────────────

def _spawn_celery_worker() -> "subprocess.Popen | None":
    """Launch a Celery worker as a child process of the API server.

    Returns the ``Popen`` handle so the lifespan can terminate it on
    shutdown, or ``None`` if the worker should not be started.

    Conditions that skip auto-start:
    - ``REDIS_URL`` is not set (falls back to BackgroundTasks mode).
    - ``CELERY_AUTO_START=false`` (useful in tests / CI).
    """
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        _log.info(
            "REDIS_URL not set — skipping Celery worker auto-start. "
            "Report processing will use FastAPI BackgroundTasks."
        )
        return None

    if os.getenv("CELERY_AUTO_START", "true").lower() in ("false", "0", "no"):
        _log.info("CELERY_AUTO_START=false — worker will not be started automatically.")
        return None

    concurrency = os.getenv("CELERY_CONCURRENCY", "2")

    # Build PYTHONPATH so the worker subprocess can do `import backend.*`
    # regardless of the cwd uvicorn was launched from.
    src_dir = str(Path(__file__).resolve().parent.parent)  # …/src
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_dir}:{existing_pp}" if existing_pp else src_dir

    cmd = [
        sys.executable, "-m", "celery",
        "-A", "backend.worker.celery_app",
        "worker",
        "--loglevel", os.getenv("CELERY_LOGLEVEL", "info"),
        "--concurrency", concurrency,
        "--hostname", "worker@%h",
        "-Q", "reports,default",
    ]

    _log.info(
        "Auto-starting Celery worker (concurrency=%s, broker=%s) …",
        concurrency, redis_url,
    )
    try:
        proc = subprocess.Popen(cmd, env=env)
        _log.info("Celery worker started (pid=%s)", proc.pid)
        return proc
    except Exception as exc:  # noqa: BLE001
        _log.error("Failed to auto-start Celery worker: %s", exc)
        return None


# ── App lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle.

    Startup:
      1. Spawn a Celery worker subprocess (when REDIS_URL is configured).
      2. Start an asyncio task that subscribes to Redis pub/sub and relays
         worker status updates to connected WebSocket clients.

    Shutdown:
      Both are cleaned up in reverse order.
    """
    # 1. Spawn worker child process
    worker_proc = _spawn_celery_worker()

    # 2. Start Redis → WebSocket relay task
    redis_task = asyncio.create_task(
        report_status_connection_manager.start_redis_subscriber(),
        name="redis-status-subscriber",
    )

    try:
        yield
    finally:
        # Stop Redis subscriber
        redis_task.cancel()
        try:
            await redis_task
        except asyncio.CancelledError:
            pass

        # Gracefully terminate the Celery worker child process
        if worker_proc is not None:
            _log.info("Shutting down Celery worker (pid=%s) …", worker_proc.pid)
            worker_proc.terminate()
            try:
                worker_proc.wait(timeout=10)
                _log.info("Celery worker exited cleanly.")
            except subprocess.TimeoutExpired:
                _log.warning("Worker did not exit in time — sending SIGKILL.")
                worker_proc.kill()


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Personal Health Assistant API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Allow frontend HTML files (served from any localhost port or file://) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5500",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8080",
        "null",  # file:// origin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/health/workers", tags=["health"])
def worker_status() -> dict:
    """Live report of connected Celery workers and their task slots.

    Uses Celery's ``inspect`` API (via Redis) to query every worker that is
    currently registered.  Returns within 2 seconds even if no workers are
    online.

    Response fields
    ---------------
    ``worker_count``
        Number of Celery worker *processes* responding right now.
    ``total_concurrency``
        Sum of all pool slots across all workers (i.e. max parallel tasks).
    ``active_tasks``
        Number of tasks currently being executed.
    ``reserved_tasks``
        Number of tasks queued locally on a worker, waiting for a free slot.
    ``workers``
        Per-worker breakdown with hostname, concurrency, active/reserved counts.
    """
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        return {
            "worker_count": 0,
            "total_concurrency": 0,
            "active_tasks": 0,
            "reserved_tasks": 0,
            "workers": [],
            "note": "REDIS_URL not configured — Celery workers are not enabled.",
        }

    try:
        from backend.worker.celery_app import celery_app
        inspector = celery_app.control.inspect(timeout=2.0)

        # Each call returns {hostname: [...]} or None if no workers respond
        stats_raw    = inspector.stats()      or {}
        active_raw   = inspector.active()     or {}
        reserved_raw = inspector.reserved()   or {}

        workers = []
        total_concurrency = 0
        total_active      = 0
        total_reserved    = 0

        for hostname, stat in stats_raw.items():
            pool      = stat.get("pool", {})
            # pool.processes is a list of PIDs — its length = concurrency
            processes = pool.get("processes", [])
            concurrency = len(processes) if processes else pool.get("max-concurrency", 0)

            active   = active_raw.get(hostname,   [])
            reserved = reserved_raw.get(hostname, [])

            total_concurrency += concurrency
            total_active      += len(active)
            total_reserved    += len(reserved)

            workers.append({
                "hostname":    hostname,
                "concurrency": concurrency,
                "pid":         stat.get("pid"),
                "active":      len(active),
                "reserved":    len(reserved),
                "active_tasks": [
                    {"id": t.get("id"), "name": t.get("name")} for t in active
                ],
            })

        return {
            "worker_count":     len(workers),
            "total_concurrency": total_concurrency,
            "active_tasks":     total_active,
            "reserved_tasks":   total_reserved,
            "workers":          workers,
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "worker_count":     0,
            "total_concurrency": 0,
            "active_tasks":     0,
            "reserved_tasks":   0,
            "workers":          [],
            "error":            str(exc),
        }

# Mount the reports router that exposes the Supabase upload endpoint.
app.include_router(reports.router)
app.include_router(reports.api_reports_router)

# Production RAG query pipeline: retrieval → context assembly → (Gemini TBD).
app.include_router(rag.router)

# Voice: Handle voice and text interactions.
app.include_router(voice.router)


@app.post("/voice_chat", include_in_schema=False)
async def legacy_voice_chat(request: Request):
    """Backward-compatible alias for older clients still calling /voice_chat."""
    return await voice.voice_chat(request)

# Alerts: fetch and evaluate deterministic health alerts per user.
app.include_router(alerts.router)

# Users: user management and profile operations.
app.include_router(users.router)

# Auth: user registration and login
app.include_router(auth.router)

# Upload: Protected structured report uploads
app.include_router(upload.router)
# Vitals: wearable device data ingestion and 7-day summary retrieval.
app.include_router(vitals.router)

# Environment: real-time AQI and weather data via Open-Meteo.
app.include_router(environment.router)

# Summaries: AI-generated weekly health summaries (generation + retrieval).
app.include_router(summaries.router)

# Debug routes for diagnostics
app.include_router(debug.router)

# Doctor dashboard: patient list, summaries, reports, alerts for assigned patients.
app.include_router(doctor.router)

# WebSocket status updates for report processing.
app.include_router(report_status_ws.router)

# Temporary RAG test route for UI citation rendering.
@app.get("/api/v1/rag/test")
async def test_rag_retrieval(user_id: str, query: str) -> dict:
    return retrieve_mock_context(user_id, query)
