#!/usr/bin/env bash
# TempTeller as a native desktop app window (via pywebview).
set -euo pipefail
cd "$(dirname "$0")"

# --- Python backend + desktop deps ------------------------------------------
if [ ! -d backend/venv ]; then
  echo "› Creating Python virtualenv…"
  python3 -m venv backend/venv
  backend/venv/bin/pip install -q --upgrade pip
fi
if ! backend/venv/bin/python3 -c "import fastapi, psutil" 2>/dev/null; then
  backend/venv/bin/pip install -q -r backend/requirements.txt
fi
if ! backend/venv/bin/python3 -c "from PyQt5.QtWebEngineWidgets import QWebEngineView" 2>/dev/null; then
  echo "› Installing desktop window dependencies (one-time, ~100MB)…"
  backend/venv/bin/pip install -q -r backend/requirements-desktop.txt
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

echo "› Launching TempTeller window…"
exec backend/venv/bin/python3 backend/desktop.py "$@"
