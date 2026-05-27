#!/usr/bin/env bash
# TempTeller launcher: sets up deps on first run, builds the UI, and serves the
# dashboard at http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"

# --- Python backend ---------------------------------------------------------
if [ ! -d backend/venv ]; then
  echo "› Creating Python virtualenv…"
  python3 -m venv backend/venv
  backend/venv/bin/pip install -q --upgrade pip
  backend/venv/bin/pip install -q -r backend/requirements.txt
fi

# --- React frontend (build once; rebuild if sources changed) ----------------
if [ ! -d frontend/node_modules ]; then
  echo "› Installing frontend dependencies…"
  (cd frontend && npm install --no-fund --no-audit)
fi
if [ ! -d frontend/dist ] || [ -n "$(find frontend/src frontend/index.html -newer frontend/dist 2>/dev/null)" ]; then
  echo "› Building dashboard…"
  (cd frontend && npm run build)
fi

echo "› TempTeller running at http://localhost:${PORT}"

# Open the dashboard in the default browser once the server is up.
if command -v xdg-open >/dev/null 2>&1; then
  ( for _ in $(seq 1 20); do
      curl -s -o /dev/null "http://localhost:${PORT}/" && break || sleep 0.3
    done
    xdg-open "http://localhost:${PORT}" >/dev/null 2>&1 ) &
fi

exec backend/venv/bin/uvicorn server:app --app-dir backend --host 0.0.0.0 --port "${PORT}"
