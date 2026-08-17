from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Any

from .provenance import capture, write_json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_no_placeholder(value: Any, name: str) -> str:
    if value is None or not str(value).strip():
        raise RuntimeError(f"Host-specific setting '{name}' is not configured")
    return str(value)


def run_shell(command: str, logfile: Path, cwd: str | None = None) -> subprocess.Popen:
    logfile.parent.mkdir(parents=True, exist_ok=True)
    f = logfile.open("w", encoding="utf-8")
    return subprocess.Popen(["bash", "-lc", command], stdout=f, stderr=subprocess.STDOUT, cwd=cwd, text=True)


def create_run_dir(root: str | Path, condition_id: str, repetition: int) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{condition_id}_r{repetition:02d}_{stamp}"
    p = Path(root) / condition_id / f"run_{repetition:02d}_{stamp}"
    for sub in ["config_snapshot", "orbital", "oai", "network", "transport", "clocks"]:
        (p / sub).mkdir(parents=True, exist_ok=True)
    (p / "run_id.txt").write_text(run_id + "\n", encoding="utf-8")
    return p


def initialize_manifest(run_dir: Path, condition_id: str, repetition: int, framework_root: Path, oai_root: str | None, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = {
        "run_id": (run_dir / "run_id.txt").read_text().strip(),
        "condition_id": condition_id,
        "repetition": repetition,
        "start_utc": utc_now(),
        "provenance": capture(framework_root, oai_root),
    }
    if extra:
        manifest.update(extra)
    write_json(manifest, run_dir / "manifest.json")
    return manifest


def finish_run(run_dir: Path, status: str, notes: str = "") -> None:
    write_json({"status": status, "end_utc": utc_now(), "notes": notes}, run_dir / "run_status.json")
