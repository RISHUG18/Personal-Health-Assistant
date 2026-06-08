#!/usr/bin/env bash
# start_worker.sh — Start one or more Celery report-processing workers.
#
# Usage
# -----
#   ./start_worker.sh                      # 4 concurrent workers (default)
#   ./start_worker.sh --concurrency 8      # 8 concurrent workers
#   ./start_worker.sh --autoscale 8,2      # auto-scale between 2 and 8
#   WORKERS=2 ./start_worker.sh            # shorthand for --concurrency 2
#
# Prerequisites
# -------------
#   1. Redis running:  redis-server  (or Docker: docker run -p 6379:6379 redis:7-alpine)
#   2. Python env active with requirements installed:
#        pip install -r requirements.txt
#   3. .env file present (this script loads it automatically).
#
# The script must be run from the ``src/backend`` directory, or PYTHONPATH
# must include the repo root so ``import backend.*`` resolves correctly.
#
# Logs
# ----
#   Worker logs go to stdout by default.  Redirect to a file if needed:
#       ./start_worker.sh 2>&1 | tee worker.log

set -euo pipefail

# ── Environment setup ─────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="/.env"

if [[ -f "$ENV_FILE" ]]; then
    # Export non-comment, non-empty lines as env vars
    set -o allexport
    # Strip leading spaces and BOM characters that might exist in .env
    # shellcheck disable=SC1090
    source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' | sed 's/^\s*//')
    set +o allexport
    echo "[worker] Loaded env from $ENV_FILE"
else
    echo "[worker] WARNING: $ENV_FILE not found — using existing shell environment"
fi

# Ensure the repo root is on PYTHONPATH so `import backend.*` works
export PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"

# ── Defaults ──────────────────────────────────────────────────────────────────
CONCURRENCY="${WORKERS:-4}"
LOGLEVEL="${CELERY_LOGLEVEL:-info}"
QUEUES="${CELERY_QUEUES:-reports,default}"
APP="backend.worker.celery_app"

# ── Parse optional CLI overrides ──────────────────────────────────────────────
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --concurrency)   CONCURRENCY="$2"; shift 2 ;;
        --autoscale)     EXTRA_ARGS+=("--autoscale=$2"); CONCURRENCY=""; shift 2 ;;
        --loglevel)      LOGLEVEL="$2"; shift 2 ;;
        --queues|-Q)     QUEUES="$2"; shift 2 ;;
        *)               EXTRA_ARGS+=("$1"); shift ;;
    esac
done

# ── Check Redis ───────────────────────────────────────────────────────────────
REDIS_URL="${REDIS_URL:-redis://localhost:6385/0}"
echo "[worker] Broker: $REDIS_URL"

if command -v redis-cli &>/dev/null; then
    REDIS_HOST="${REDIS_URL#*://}"
    REDIS_HOST="${REDIS_HOST%%:*}"
    REDIS_PORT="${REDIS_URL##*:}"
    REDIS_PORT="${REDIS_PORT%%/*}"
    if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &>/dev/null; then
        echo "[worker] ERROR: Redis is not reachable at $REDIS_URL"
        echo "         Start Redis with:  redis-server"
        echo "         Or via Docker:     docker run -p 6379:6379 redis:7-alpine"
        exit 1
    fi
    echo "[worker] Redis ping OK"
fi

# ── Launch ────────────────────────────────────────────────────────────────────
CELERY_CMD=(
    celery -A "$APP" worker
    --loglevel="$LOGLEVEL"
    --queues="$QUEUES"
    --hostname="worker@%h"
    "${EXTRA_ARGS[@]}"
)

if [[ -n "$CONCURRENCY" ]]; then
    CELERY_CMD+=(--concurrency="$CONCURRENCY")
fi

echo "[worker] Starting Celery worker (concurrency=${CONCURRENCY:-auto}, queues=$QUEUES)"
echo "[worker] Command: ${CELERY_CMD[*]}"
echo ""

exec "${CELERY_CMD[@]}"
