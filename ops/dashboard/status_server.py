#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

OPS_ROOT = Path(os.environ.get("CAQF_OPS_ROOT", str(Path.home() / "codex-caqf")))
REPO_ROOT = Path(os.environ.get("CAQF_ROOT", str(Path.home() / "Predictive-CAQF-5G-NTN-Experiments")))
STATIC_ROOT = Path(__file__).resolve().parent


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {} if default is None else default


def run_counts():
    candidates = [REPO_ROOT / "results" / "run_index.csv", REPO_ROOT / "results" / "final" / "run_index.csv", OPS_ROOT / "state" / "run_index.csv"]
    path = next((p for p in candidates if p.exists()), None)
    counts = {"completed": 0, "valid": 0, "invalid": 0, "failed": 0}
    if not path:
        return counts
    try:
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                st = (row.get("status") or "").upper()
                if st in {"DONE", "VALID", "COMPLETE", "COMPLETED"}:
                    counts["completed"] += 1; counts["valid"] += 1
                elif "INVALID" in st: counts["invalid"] += 1
                elif "FAIL" in st or "ERROR" in st: counts["failed"] += 1
    except Exception:
        pass
    return counts


def aggregate(write_snapshot: bool = True):
    state = OPS_ROOT / "state"
    campaign = read_json(state / "campaign_status.json")
    for k, v in run_counts().items():
        campaign.setdefault(k, v)
    obj = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "campaign": campaign,
        "current": read_json(state / "current_run.json"),
        "watchdog": read_json(state / "watchdog_health.json"),
        "health": read_json(state / "ran_health.json"),
        "drive": read_json(state / "drive_health.json"),
        "recent_event": read_json(state / "recent_event.json"),
    }
    if write_snapshot:
        try:
            state.mkdir(parents=True, exist_ok=True)
            (state / "dashboard_snapshot.json").write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass
    return obj


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self):
        if urlparse(self.path).path == "/api/status":
            payload = json.dumps(aggregate(), indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers(); self.wfile.write(payload); return
        return super().do_GET()


if __name__ == "__main__":
    host = os.environ.get("CAQF_DASHBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("CAQF_DASHBOARD_PORT", "8765"))
    OPS_ROOT.joinpath("state").mkdir(parents=True, exist_ok=True)
    aggregate()
    print(f"CA-QF dashboard: http://{host}:{port}/")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
