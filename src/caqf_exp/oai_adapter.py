from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class OAIAdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class OAIPaths:
    root: Path
    gnb_config: Path | None = None
    ue_config: Path | None = None


def require_path(value: str | None, label: str) -> Path:
    if not value:
        raise OAIAdapterError(f"Missing host-specific OAI setting: {label}")
    p = Path(value)
    if not p.exists():
        raise OAIAdapterError(f"Configured {label} does not exist: {p}")
    return p


def render_command(template: str | None, **values: Any) -> str:
    """Render a host-discovered command template without inventing defaults.

    Codex should populate templates only after confirming commands on the RAN host.
    Scientific condition meaning belongs in campaign/config files, not inside ad-hoc
    shell history.
    """
    if not template:
        raise OAIAdapterError("OAI command template is not configured")
    try:
        return template.format(**values)
    except KeyError as exc:
        raise OAIAdapterError(f"Missing template value: {exc.args[0]}") from exc


def assert_separate_study_checkout(active_oai: str, prior_oai: str | None) -> None:
    active = Path(active_oai).resolve()
    if prior_oai and active == Path(prior_oai).resolve():
        raise OAIAdapterError(
            "Active CA-QF OAI checkout resolves to the prior completed study checkout. "
            "Create a separate checkout before editing."
        )
