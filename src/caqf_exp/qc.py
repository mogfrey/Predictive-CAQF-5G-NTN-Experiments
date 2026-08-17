from __future__ import annotations

from pathlib import Path
import json
from typing import Any

VALID_STATUSES = {"valid_success", "condition_induced_failure", "invalid_lab_failure", "operator_error", "instrumentation_failure"}


def check_run_dir(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    required = ["manifest.json", "run_status.json", "oai/gnb.log", "oai/ue.log"]
    missing = [x for x in required if not (p / x).exists()]
    status = None
    if (p / "run_status.json").exists():
        try:
            status = json.loads((p / "run_status.json").read_text(encoding="utf-8")).get("status")
        except Exception:
            status = "unreadable"
    return {
        "run_dir": str(p),
        "missing": missing,
        "status": status,
        "status_valid": status in VALID_STATUSES,
        "pass": not missing and status in VALID_STATUSES,
    }
