# TempTeller

A sleek, real-time system dashboard for Linux. SVG speedometer gauges for
temperatures, CPU and RAM usage, plus the top 5 processes — all streamed live
over a WebSocket and rendered in React. Fully responsive: the gauge grid
reflows and scales as you resize the window.

## Stack
- **Backend** — FastAPI + `psutil` + `lm-sensors`, pushing a JSON snapshot every second.
- **Frontend** — React (Vite), hand-built scalable SVG gauges.

## Run

**As a desktop app** (native window, recommended): double-click the
**TempTeller** icon on your desktop / in the app menu, or run:
```bash
./run-desktop.sh
```
Opens in its own resizable window with a **system-tray icon** (lower-right).
Closing the window hides it to the tray instead of quitting; left-click the
tray icon to show/hide, right-click for a menu (Show/Hide, Quit). First run
installs the window toolkit (Qt, ~100 MB, one time).

**As a web dashboard** (in your browser):
```bash
./run.sh
```
Then open http://localhost:8000 (it also auto-opens your browser).

First run installs dependencies and builds the UI (a minute or two); later runs
start instantly. Run only one of the two at a time — they share port 8000.

Requirements: `python3`, `node`/`npm`, and `lm-sensors` (`sudo apt install lm-sensors`,
then `sudo sensors-detect`).

## Desktop icon, app-menu entry & autostart
```bash
./install.sh
```
Generates and installs (for the current user) a double-clickable desktop icon,
an app-menu entry, the tray icon, and an autostart entry that launches
TempTeller hidden in the tray on login. All paths are derived automatically —
nothing is hardcoded. Re-run it any time you move the project folder.

## Development (hot reload)
```bash
# terminal 1 — backend
backend/venv/bin/uvicorn server:app --app-dir backend --reload

# terminal 2 — frontend with hot reload (proxies /ws to the backend)
cd frontend && npm run dev   # http://localhost:5173
```

