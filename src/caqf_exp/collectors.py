from __future__ import annotations

from pathlib import Path
import json
import re
import pandas as pd


def iperf_udp_intervals(json_path: str | Path) -> pd.DataFrame:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    rows = []
    for item in data.get("intervals", []):
        summary = item.get("sum") or (item.get("streams") or [{}])[0].get("udp", {})
        if not summary:
            continue
        rows.append({
            "t_start_s": summary.get("start"),
            "t_end_s": summary.get("end"),
            "seconds": summary.get("seconds"),
            "goodput_mbps": (summary.get("bits_per_second") / 1e6) if summary.get("bits_per_second") is not None else None,
            "jitter_ms": summary.get("jitter_ms"),
            "lost_packets": summary.get("lost_packets"),
            "packets": summary.get("packets"),
            "loss_fraction": (summary.get("lost_percent") / 100.0) if summary.get("lost_percent") is not None else None,
        })
    return pd.DataFrame(rows)


def parse_ping_rtt(text_path: str | Path) -> pd.DataFrame:
    # Handles standard iputils lines containing time=<ms>. Timestamping should be
    # added by the host collector; this parser provides run-relative sequence only.
    pattern = re.compile(r"icmp_seq=(\d+).*?time[=<]([0-9.]+)\s*ms")
    rows = []
    for line in Path(text_path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.search(line)
        if m:
            rows.append({"icmp_seq": int(m.group(1)), "rtt_ms": float(m.group(2))})
    return pd.DataFrame(rows)


def qos_feasibility(intervals: pd.DataFrame, offered_rate_mbps: float, goodput_fraction_min: float, loss_fraction_max: float) -> pd.DataFrame:
    out = intervals.copy()
    out["qos_feasible"] = (
        (out["goodput_mbps"] >= goodput_fraction_min * offered_rate_mbps)
        & (out["loss_fraction"] <= loss_fraction_max)
    )
    return out


def first_persistent_failure(feasible: pd.Series, persistence_windows: int = 2) -> int | None:
    fail = (~feasible.fillna(False)).astype(int)
    roll = fail.rolling(persistence_windows, min_periods=persistence_windows).sum()
    hits = roll[roll >= persistence_windows]
    if hits.empty:
        return None
    return int(hits.index[0] - persistence_windows + 1)
