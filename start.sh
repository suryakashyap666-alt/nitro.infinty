#!/usr/bin/env bash
#
# start.sh — runs ai-backend (FastAPI, :8000) and web-client (React, :3000)
# concurrently, and cleanly kills both when the script is interrupted.

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

# --- 1. Backend: FastAPI on :8000 ---
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
  echo "==> No requirements.txt found; installing minimal runtime deps..."
  pip install --quiet --disable-pip-version-check fastapi "uvicorn[standard]" httpx pydantic
fi

echo "==> Launching ai-backend on port $BACKEND_PORT..."
PYTHONPATH="$BACKEND_DIR" uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

deactivate
cd "$PROJECT_ROOT"

# --- 2. Frontend: React (Create React App) on :3000 ---
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
# web-client is a Create React App (react-scripts) project: it takes its
# port from the PORT env var via "npm start", not a --port flag. It also
# proxies non-API requests to the backend during dev via package.json's
# "proxy" field, but REACT_APP_API_URL below is what App.js actually uses
# to build the /api/v1/chat endpoint, so it must point at the backend
# explicitly for the SSE fetch() call to work.
REACT_APP_API_URL="http://localhost:$BACKEND_PORT" PORT="$FRONTEND_PORT" BROWSER=none npm start &
FRONTEND_PID=$!

cd "$PROJECT_ROOT"

echo ""
echo "==> ai-backend running:  http://localhost:$BACKEND_PORT  (pid $BACKEND_PID)"
echo "==> web-client running:  http://localhost:$FRONTEND_PORT (pid $FRONTEND_PID)"
echo "==> Press Ctrl+C to stop both services."
echo ""

# Wait on both; if either exits unexpectedly, tear down the other via the trap.
wait -n "$BACKEND_PID" "$FRONTEND_PID"
cleanup