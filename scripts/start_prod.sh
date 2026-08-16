#!/usr/bin/env bash
set -euo pipefail
# Build frontend and start backend (serve frontend from FastAPI)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PATH="/home/lakshya-kashyap/.venvs/nitro-ai"
FRONTEND_DIR="$REPO_ROOT/frontend"
LOG_DIR="$REPO_ROOT/logs"
RUN_DIR="$REPO_ROOT/run"

NITRO_HOST="${NITRO_HOST:-0.0.0.0}"
NITRO_PORT="${NITRO_PORT:-8000}"

mkdir -p "$LOG_DIR" "$RUN_DIR"

if [ ! -f "$VENV_PATH/bin/activate" ]; then
  echo "ERROR: virtualenv not found at $VENV_PATH" >&2
  exit 2
fi

echo "Building frontend (production)..."
# Use node directly to avoid noexec on external mounts
cd "$FRONTEND_DIR"
if [ -x "$(command -v node)" ] && [ -d node_modules/react-scripts ]; then
  node node_modules/react-scripts/bin/react-scripts.js build
else
  echo "Node or react-scripts not found. Run 'npm install' in $FRONTEND_DIR or use a machine with Node installed." >&2
  exit 3
fi

# Activate venv and start uvicorn (serves frontend build under backend/main.py)
source "$VENV_PATH/bin/activate"
cd "$REPO_ROOT"

echo "Starting backend (uvicorn) on $NITRO_HOST:$NITRO_PORT..."
nohup python -m uvicorn backend.main:app --host "$NITRO_HOST" --port "$NITRO_PORT" > "$LOG_DIR/uvicorn.log" 2>&1 &
PID=$!
echo $PID > "$RUN_DIR/nitro.pid"

echo "Started (pid=$PID). Logs: $LOG_DIR/uvicorn.log"

exit 0
