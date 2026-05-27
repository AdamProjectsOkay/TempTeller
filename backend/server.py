"""TempTeller backend: streams system temps, CPU, RAM and top processes over a WebSocket."""
import asyncio
import glob
import json
import os
import subprocess
import time
from pathlib import Path

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="TempTeller")


# --- Sensor parsing ---------------------------------------------------------

def parse_sensors():
    """Return {chip: {feature: {"value": float, "max": float}}} from `sensors -j`."""
    try:
        out = subprocess.run(
            ["sensors", "-j"], capture_output=True, text=True, timeout=2
        ).stdout
        data = json.loads(out)
    except Exception:
        return {}

    parsed = {}
    for chip, features in data.items():
        if not isinstance(features, dict):
            continue
        for feature, readings in features.items():
            if not isinstance(readings, dict):
                continue
            value = crit = None
            for key, val in readings.items():
                if key.endswith("_input") and "temp" in key:
                    value = val
                elif key.endswith("_crit"):
                    crit = val
                elif key.endswith("_max") and crit is None:
                    crit = val
            if value is None:
                continue
            # Ignore unset alarm registers (e.g. 65261) and other nonsense maxes.
            limit = crit if crit and 40 < crit <= 150 else 100
            parsed.setdefault(chip, {})[feature] = {
                "value": round(value, 1), "max": limit,
            }
    return parsed


def _find(parsed, prefix, features):
    """First reading on a chip matching `prefix` for any of `features`, in order."""
    for chip, feats in parsed.items():
        if chip.startswith(prefix):
            for f in features:
                if f in feats:
                    return feats[f]
    return None


def gpu_usage():
    """Discrete-GPU utilization (%) from sysfs; prefers the card with most VRAM."""
    best = best_vram = None
    fallback = None
    for dev in glob.glob("/sys/class/drm/card*/device"):
        try:
            busy = int(open(os.path.join(dev, "gpu_busy_percent")).read().strip())
        except (OSError, ValueError):
            continue
        fallback = busy
        try:
            vram = int(open(os.path.join(dev, "mem_info_vram_total")).read().strip())
        except (OSError, ValueError):
            vram = 0
        if best_vram is None or vram > best_vram:
            best_vram, best = vram, busy
    return best if best is not None else fallback


def build_dials(parsed, cpu_pct, ram_pct):
    """Curated double-dials: outer ring = temperature, inner ring = usage."""
    dials = []

    cpu_t = _find(parsed, "k10temp", ["Tctl"]) or _find(
        parsed, "coretemp", ["Package id 0", "temp1"])
    if cpu_t:
        dials.append({"label": "CPU", "temp": cpu_t["value"],
                      "tempMax": cpu_t["max"], "usage": cpu_pct})

    # The discrete GPU is the chip exposing a 'junction' reading.
    gpu_t = None
    for chip, feats in parsed.items():
        if chip.startswith(("amdgpu", "nouveau", "nvidia", "radeon")) and "junction" in feats:
            gpu_t = feats["junction"]
            break
    gpu_t = gpu_t or _find(parsed, "amdgpu", ["edge", "temp1"])
    if gpu_t:
        dials.append({"label": "GPU", "temp": gpu_t["value"],
                      "tempMax": gpu_t["max"], "usage": gpu_usage()})

    # Average across DIMM temperature sensors, if present.
    dimm = [f["value"] for chip, feats in parsed.items()
            if chip.startswith("spd5118") for f in feats.values()]
    if dimm:
        dials.append({"label": "Memory", "temp": round(sum(dimm) / len(dimm), 1),
                      "tempMax": 85, "usage": ram_pct})

    return dials


# --- System metrics ---------------------------------------------------------

def read_metrics(include_procs=True):
    vm = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=None)
    parsed = parse_sensors()
    return {
        "ts": time.time(),
        "cpu": {
            "percent": cpu_pct,
            "freq": round((psutil.cpu_freq().current or 0) / 1000, 2),
            "cores": psutil.cpu_count(logical=True),
        },
        "ram": {
            "percent": vm.percent,
            "used_gb": round(vm.used / 1e9, 1),
            "total_gb": round(vm.total / 1e9, 1),
        },
        "dials": build_dials(parsed, cpu_pct, vm.percent),
        # Processes refresh every 5s (see ws loop); None means "keep the last list".
        "processes": top_processes() if include_procs else None,
    }


def top_processes(n=5):
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "memory_info"]):
        info = p.info
        rss = info["memory_info"].rss if info["memory_info"] else 0
        procs.append({
            "pid": info["pid"],
            "name": info["name"] or "?",
            "cpu": round(info["cpu_percent"] or 0, 1),
            "mem": round(info["memory_percent"] or 0, 1),
            "mem_mb": round(rss / 1e6),
        })
    procs.sort(key=lambda x: x["cpu"], reverse=True)
    return procs[:n]


# Prime per-process and system CPU counters so the first reading is meaningful.
psutil.cpu_percent(interval=None)
for p in psutil.process_iter():
    try:
        p.cpu_percent(None)
    except psutil.Error:
        pass


# --- WebSocket + static serving ---------------------------------------------

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    tick = 0
    try:
        while True:
            await websocket.send_json(read_metrics(include_procs=(tick % 5 == 0)))
            tick += 1
            await asyncio.sleep(1.0)
    except (WebSocketDisconnect, RuntimeError):
        pass


DIST = Path(__file__).parent.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    async def index():
        return FileResponse(DIST / "index.html")
