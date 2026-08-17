from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import asin, atan2, cos, pi, sin, sqrt
from pathlib import Path
from typing import Iterable

from sgp4.api import Satrec, jday

C = 299_792_458.0
EARTH_RADIUS_M = 6_378_137.0
EARTH_ROT_RATE = 7.2921150e-5


@dataclass(frozen=True)
class TLE:
    name: str
    line1: str
    line2: str


def read_tles(path: str | Path) -> list[TLE]:
    lines = [x.strip() for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]
    out: list[TLE] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("1 "):
            name = lines[i][2:7]
            line1, line2 = lines[i], lines[i + 1]
            i += 2
        else:
            name, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
            i += 3
        out.append(TLE(name=name, line1=line1, line2=line2))
    return out


def _gmst_rad(dt: datetime) -> float:
    dt = dt.astimezone(timezone.utc)
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    d = (jd + fr) - 2451545.0
    return (280.46061837 + 360.98564736629 * d) * pi / 180.0 % (2 * pi)


def _geodetic_ecef(lat_deg: float, lon_deg: float, alt_m: float) -> tuple[float, float, float]:
    lat, lon = lat_deg * pi / 180, lon_deg * pi / 180
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    a = EARTH_RADIUS_M
    n = a / sqrt(1 - e2 * sin(lat) ** 2)
    return ((n + alt_m) * cos(lat) * cos(lon),
            (n + alt_m) * cos(lat) * sin(lon),
            (n * (1 - e2) + alt_m) * sin(lat))


def _teme_to_ecef(r_km: Iterable[float], v_km_s: Iterable[float], dt: datetime) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    th = _gmst_rad(dt)
    c, s = cos(th), sin(th)
    rx, ry, rz = [x * 1000 for x in r_km]
    vx, vy, vz = [x * 1000 for x in v_km_s]
    r = (c * rx + s * ry, -s * rx + c * ry, rz)
    v_rot = (c * vx + s * vy, -s * vx + c * vy, vz)
    omega_cross_r = (-EARTH_ROT_RATE * r[1], EARTH_ROT_RATE * r[0], 0.0)
    v = tuple(v_rot[i] - omega_cross_r[i] for i in range(3))
    return r, v


def state(tle: TLE, dt: datetime, lat_deg: float, lon_deg: float, alt_m: float, carrier_hz: float) -> dict[str, float]:
    sat = Satrec.twoline2rv(tle.line1, tle.line2)
    dt = dt.astimezone(timezone.utc)
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    err, r_km, v_km_s = sat.sgp4(jd, fr)
    if err:
        raise RuntimeError(f"SGP4 error {err} for {tle.name} at {dt.isoformat()}")
    r, v = _teme_to_ecef(r_km, v_km_s, dt)
    obs = _geodetic_ecef(lat_deg, lon_deg, alt_m)
    rho = tuple(r[i] - obs[i] for i in range(3))
    rng = sqrt(sum(x * x for x in rho))
    los = tuple(x / rng for x in rho)
    range_rate = sum(v[i] * los[i] for i in range(3))

    lat, lon = lat_deg * pi / 180, lon_deg * pi / 180
    east = (-sin(lon), cos(lon), 0.0)
    north = (-sin(lat) * cos(lon), -sin(lat) * sin(lon), cos(lat))
    up = (cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat))
    e = sum(rho[i] * east[i] for i in range(3))
    n = sum(rho[i] * north[i] for i in range(3))
    u = sum(rho[i] * up[i] for i in range(3))
    elevation = asin(u / rng) * 180 / pi
    azimuth = atan2(e, n) * 180 / pi % 360
    doppler = -carrier_hz * range_rate / C
    return {
        "elevation_deg": elevation,
        "azimuth_deg": azimuth,
        "slant_range_m": rng,
        "range_rate_mps": range_rate,
        "geometric_delay_ms": rng / C * 1000,
        "doppler_hz": doppler,
        "sat_x_m": r[0], "sat_y_m": r[1], "sat_z_m": r[2],
        "sat_vx_mps": v[0], "sat_vy_mps": v[1], "sat_vz_mps": v[2],
    }
