#!/usr/bin/env bash
#
# start.sh — Starts ai-backend (:8000) and web-client (:3000) concurrently.
# Cleanly terminates all child processes upon Exit / Ctrl+C.

set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/ai-backend"
FRONTEND_DIR="$PROJECT_ROOT/web-client"

BACKEND_PORT=8000
FRONTEND_PORT=3000

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "==> Shutting down Nitro Infinity AI services..."

  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "    stopping ai-backend (pid $BACKEND_PID)"
    kill "$BACKEND_PID" 2>/dev/null
    wait "$BACKEND_PID" 2>/dev/null
  fi

  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "    stopping web-client (pid $FRONTEND_PID)"
    kill "$FRONTEND_PID" 2>/dev/null
    wait "$FRONTEND_PID" 2>/dev/null
  fi

  echo "==> Clean shutdown complete."
  exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo "==> Starting Nitro Infinity AI (ai-backend + web-client)"

# 1. Backend: FastAPI on :8000
if [ ! -d "$BACKEND_DIR" ]; then
  echo "ERROR: $BACKEND_DIR not found." >&2
  exit 1
fi

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
  echo "==> Creating Python virtualenv for ai-backend..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if [ -f "requirements.txt" ]; then
  pip install --quiet --disable-pip-version-check -r requirements.txt
else
  pip install --quiet --disable-pip-version-check fastapi "uvicorn[standard]" httpx pydantic
fi

echo "==> Launching ai-backend on port $BACKEND_PORT..."
PYTHONPATH="$BACKEND_DIR" uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

deactivate
cd "$PROJECT_ROOT"

# 2. Frontend: React on :3000
if [ ! -d "$FRONTEND_DIR" ]; then
  echo "ERROR: $FRONTEND_DIR not found." >&2
  kill "$BACKEND_PID" 2>/dev/null
  exit 1
fi

cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
  echo "==> Installing web-client dependencies..."
  npm install --silent
fi

echo "==> Launching web-client on port $FRONTEND_PORT..."
REACT_APP_API_URL="http://localhost:$BACKEND_PORT" PORT="$FRONTEND_PORT" BROWSER=none npm start &
FRONTEND_PID=$!

cd "$PROJECT_ROOT"

echo ""
echo "==> ai-backend running:  http://localhost:$BACKEND_PORT  (pid $BACKEND_PID)"
echo "==> web-client running:  http://localhost:$FRONTEND_PORT (pid $FRONTEND_PID)"
echo "==> Press Ctrl+C to stop both services."
echo ""

wait -n "$BACKEND_PID" "$FRONTEND_PID"
cleanup