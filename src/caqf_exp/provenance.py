from __future__ import annotations

from pathlib import Path
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from typing import Any


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(root: str | Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def capture(framework_root: str | Path, oai_root: str | Path | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "framework_commit": _git(framework_root, "rev-parse", "HEAD"),
        "framework_dirty": _git(framework_root, "status", "--porcelain=v1"),
    }
    if oai_root:
        result.update({
            "oai_root": str(oai_root),
            "oai_commit": _git(oai_root, "rev-parse", "HEAD"),
            "oai_describe": _git(oai_root, "describe", "--tags", "--always", "--dirty"),
            "oai_dirty": _git(oai_root, "status", "--porcelain=v1"),
        })
    return result


def write_json(data: dict[str, Any], output: str | Path) -> None:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
