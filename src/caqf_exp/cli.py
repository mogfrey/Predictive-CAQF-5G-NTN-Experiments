from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from .config import assert_campaign_valid, load_yaml
from .evaluate import leave_one_pass_out
from .features import add_history_features, build_horizon_labels
from .orbit import read_tles, state
from .pass_selection import find_passes, select_bands
from .provenance import capture, write_json
from .qc import check_run_dir


def parse_utc(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def cmd_validate_config(args):
    campaign = load_yaml(args.campaign)
    assert_campaign_valid(campaign)
    print("PASS: campaign scientific invariants validated")


def cmd_preflight(args):
    tb = load_yaml(args.testbed)
    checks = {
        "experiment_root_exists": Path(tb["paths"]["experiment_root"]).exists(),
        "oai_root_configured": bool(tb["paths"].get("oai_root")),
        "observer_configured": all(tb.get("observer", {}).get(k) is not None for k in ["latitude_deg", "longitude_deg", "altitude_m"]),
        "carrier_configured": tb.get("radio", {}).get("nr_carrier_hz") is not None,
    }
    print(json.dumps(checks, indent=2))
    if not all(checks.values()):
        raise SystemExit(2)


def cmd_provenance(args):
    data = capture(args.framework_root, args.oai_root)
    write_json(data, args.output)
    print(args.output)


def cmd_select_passes(args):
    campaign = load_yaml(args.campaign)
    assert_campaign_valid(campaign)
    tles = read_tles(args.tle_file)
    bands = campaign["tle_campaign"]["bands"]
    passes = find_passes(tles, parse_utc(args.start), args.horizon_hours, args.step_s,
                         args.lat, args.lon, args.alt_m, args.carrier_hz,
                         campaign["tle_campaign"]["elevation_mask_deg"])
    selected = select_bands(passes, bands)
    write_json({"source_tle": args.tle_file, "start_utc": args.start, "selected": selected}, args.output)
    print(args.output)


def cmd_tle_trace(args):
    tles = read_tles(args.tle_file)
    tle = next((x for x in tles if args.satellite.lower() in x.name.lower() or args.satellite in x.line1), None)
    if tle is None:
        raise SystemExit(f"Satellite not found: {args.satellite}")
    start = parse_utc(args.start)
    rows = []
    for i in range(0, args.duration_s + 1, args.step_s):
        t = start + timedelta(seconds=i)
        s = state(tle, t, args.lat, args.lon, args.alt_m, args.carrier_hz)
        rows.append({"t_s": i, "utc": t.isoformat(), "satellite": tle.name, **s})
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    print(out)


def cmd_features(args):
    campaign = load_yaml(args.campaign)
    pred = load_yaml(args.predictor)
    df = pd.read_csv(args.input)
    df = add_history_features(df, pred["history_windows_s"], pred["snapshot_interval_s"])
    df = build_horizon_labels(df, campaign["scientific"]["t_req_s"])
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(args.output)


def cmd_evaluate(args):
    campaign = load_yaml(args.campaign)
    df = pd.read_csv(args.input)
    families = ["orbital", "radio_qos", "orbital_radio_qos"]
    all_p, all_f = [], []
    for fam in families:
        p, f = leave_one_pass_out(df, fam, campaign["scientific"]["t_req_s"], campaign["scientific"]["primary_continue_probability"])
        if not p.empty:
            all_p.append(p)
        if not f.empty:
            all_f.append(f)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pd.concat(all_p, ignore_index=True).to_csv(out / "predictions.csv", index=False) if all_p else pd.DataFrame().to_csv(out / "predictions.csv", index=False)
    pd.concat(all_f, ignore_index=True).to_csv(out / "fold_metrics.csv", index=False) if all_f else pd.DataFrame().to_csv(out / "fold_metrics.csv", index=False)
    print(out)


def cmd_qc_run(args):
    result = check_run_dir(args.run_dir)
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(2)


def build_parser():
    p = argparse.ArgumentParser(prog="caqf-exp")
    sub = p.add_subparsers(dest="cmd", required=True)

    x = sub.add_parser("validate-config"); x.add_argument("--campaign", required=True); x.set_defaults(func=cmd_validate_config)
    x = sub.add_parser("preflight"); x.add_argument("--testbed", required=True); x.set_defaults(func=cmd_preflight)
    x = sub.add_parser("provenance"); x.add_argument("--framework-root", default="."); x.add_argument("--oai-root"); x.add_argument("--output", required=True); x.set_defaults(func=cmd_provenance)

    x = sub.add_parser("select-passes")
    x.add_argument("--campaign", default="config/campaign.yaml"); x.add_argument("--tle-file", required=True); x.add_argument("--start", required=True)
    x.add_argument("--horizon-hours", type=float, default=48); x.add_argument("--step-s", type=int, default=10)
    x.add_argument("--lat", type=float, required=True); x.add_argument("--lon", type=float, required=True); x.add_argument("--alt-m", type=float, required=True)
    x.add_argument("--carrier-hz", type=float, required=True); x.add_argument("--output", required=True); x.set_defaults(func=cmd_select_passes)

    x = sub.add_parser("tle-trace")
    x.add_argument("--tle-file", required=True); x.add_argument("--satellite", required=True); x.add_argument("--start", required=True)
    x.add_argument("--duration-s", type=int, required=True); x.add_argument("--step-s", type=int, default=1)
    x.add_argument("--lat", type=float, required=True); x.add_argument("--lon", type=float, required=True); x.add_argument("--alt-m", type=float, required=True)
    x.add_argument("--carrier-hz", type=float, required=True); x.add_argument("--output", required=True); x.set_defaults(func=cmd_tle_trace)

    x = sub.add_parser("features"); x.add_argument("--campaign", default="config/campaign.yaml"); x.add_argument("--predictor", default="config/predictor.yaml"); x.add_argument("--input", required=True); x.add_argument("--output", required=True); x.set_defaults(func=cmd_features)
    x = sub.add_parser("evaluate"); x.add_argument("--campaign", default="config/campaign.yaml"); x.add_argument("--input", required=True); x.add_argument("--output-dir", required=True); x.set_defaults(func=cmd_evaluate)
    x = sub.add_parser("qc-run"); x.add_argument("--run-dir", required=True); x.set_defaults(func=cmd_qc_run)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
