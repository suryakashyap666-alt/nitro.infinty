#!/usr/bin/env bash
set -euo pipefail
# Start Nitro Infinity AI backend in background using venv
# Adjust VENV_PATH if your virtualenv is in a different location.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PATH="/home/lakshya-kashyap/.venvs/nitro-ai"
LOG_DIR="$REPO_ROOT/logs"
RUN_DIR="$REPO_ROOT/run"

mkdir -p "$LOG_DIR" "$RUN_DIR"

if [ ! -x "$VENV_PATH/bin/activate" ]; then
  echo "ERROR: virtualenv not found at $VENV_PATH" >&2
  exit 2
fi

echo "Starting Nitro Infinity AI backend..."
source "$VENV_PATH/bin/activate"
cd "$REPO_ROOT"

# Use nohup so process survives terminal close; write pid file.
nohup python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 > "$LOG_DIR/uvicorn.log" 2>&1 &
PID=$!
echo $PID > "$RUN_DIR/nitro.pid"
echo "Started (pid=$PID). Logs: $LOG_DIR/uvicorn.log"

exit 0
