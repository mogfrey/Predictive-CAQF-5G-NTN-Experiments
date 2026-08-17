from __future__ import annotations

import numpy as np
import pandas as pd

ORBITAL = ["elevation_deg", "slant_range_m", "range_rate_mps", "geometric_delay_ms", "doppler_hz"]
RADIO = ["bler", "dtx_count", "harq_retx_count", "mcs", "sinr_db", "ul_failure_flag", "out_of_sync_flag"]
QOS = ["goodput_mbps", "loss_fraction", "rtt_ms"]


def add_history_features(df: pd.DataFrame, windows_s: list[int], interval_s: int = 1) -> pd.DataFrame:
    out = df.sort_values(["run_id", "t_s"]).copy()
    base = [c for c in RADIO + QOS if c in out.columns]
    grouped = out.groupby("run_id", sort=False)
    for col in base:
        for w in windows_s:
            n = max(1, int(w / interval_s))
            out[f"{col}_mean_{w}s"] = grouped[col].transform(lambda s: s.rolling(n, min_periods=1).mean())
            out[f"{col}_slope_{w}s"] = grouped[col].transform(lambda s: s.diff().rolling(n, min_periods=1).mean())
    return out


def build_horizon_labels(df: pd.DataFrame, horizons_s: list[int]) -> pd.DataFrame:
    out = df.sort_values(["run_id", "t_s"]).copy()
    event_time = out.loc[out.get("event_qos_termination", 0).astype(bool)].groupby("run_id")["t_s"].min()
    max_time = out.groupby("run_id")["t_s"].max()
    for h in horizons_s:
        labels = []
        eligible = []
        for row in out.itertuples():
            rid, t = row.run_id, float(row.t_s)
            e = event_time.get(rid, np.nan)
            censor = float(max_time[rid])
            if not np.isnan(e):
                labels.append(int(e - t >= h))
                eligible.append(t <= e)
            else:
                labels.append(1 if censor - t >= h else np.nan)
                eligible.append(censor - t >= h)
        out[f"survive_{h}s"] = labels
        out[f"eligible_{h}s"] = eligible
    return out


def columns_for_family(df: pd.DataFrame, family: str) -> list[str]:
    hist = [c for c in df.columns if "_mean_" in c or "_slope_" in c]
    if family == "orbital":
        cols = ORBITAL
    elif family == "radio_qos":
        cols = RADIO + QOS + hist
    elif family == "orbital_radio_qos":
        cols = ORBITAL + RADIO + QOS + hist
    elif family == "current_qos_only":
        cols = QOS
    else:
        raise ValueError(f"Unknown feature family: {family}")
    return [c for c in cols if c in df.columns and not df[c].isna().all()]
