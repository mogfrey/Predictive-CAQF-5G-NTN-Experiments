from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .orbit import TLE, state


def find_passes(tles: list[TLE], start: datetime, horizon_h: float, step_s: int,
                lat: float, lon: float, alt_m: float, carrier_hz: float,
                elevation_mask_deg: float) -> list[dict[str, Any]]:
    start = start.astimezone(timezone.utc)
    end = start + timedelta(hours=horizon_h)
    passes: list[dict[str, Any]] = []
    for tle in tles:
        in_pass = False
        cur: dict[str, Any] | None = None
        t = start
        while t <= end:
            s = state(tle, t, lat, lon, alt_m, carrier_hz)
            vis = s["elevation_deg"] >= elevation_mask_deg
            if vis and not in_pass:
                cur = {"satellite": tle.name, "aos_utc": t.isoformat(), "max_elevation_deg": s["elevation_deg"], "tca_utc": t.isoformat()}
                in_pass = True
            if vis and cur is not None and s["elevation_deg"] > cur["max_elevation_deg"]:
                cur["max_elevation_deg"] = s["elevation_deg"]
                cur["tca_utc"] = t.isoformat()
            if in_pass and not vis and cur is not None:
                cur["los_utc"] = t.isoformat()
                passes.append(cur)
                in_pass = False
                cur = None
            t += timedelta(seconds=step_s)
    return sorted(passes, key=lambda x: x["aos_utc"])


def select_bands(passes: list[dict[str, Any]], bands: dict[str, dict[str, float]]) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for band, limits in bands.items():
        lo = limits["max_elevation_deg_min"]
        hi = limits["max_elevation_deg_max"]
        match = next((p for p in passes if lo <= p["max_elevation_deg"] <= hi), None)
        if match is None:
            raise RuntimeError(f"No pass found for {band} band [{lo}, {hi}] deg")
        selected[band] = match
    return selected
