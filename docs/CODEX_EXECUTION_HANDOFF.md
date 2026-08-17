# CODEX_EXECUTION_HANDOFF.md
## Predictive CA-QF 5G NTN — Initial Codex CLI laboratory handoff

## 1. Current checkpoint

The scientific design is approved and frozen in `docs/SCIENTIFIC_CONTRACT.md`. The public repository now contains campaign configuration, TLE/SGP4 pass/trace tooling, provenance/QC utilities, causal feature construction, whole-pass-holdout reference evaluation, an unattended watchdog scaffold, and operator/mission documents.

No CA-QF confirmatory laboratory runs have been performed from this repository yet. First task is laboratory integration and preservation, not batch execution.

## 2. Approved objective

Execute the 55-run campaign without changing scientific meaning: 25 controlled runs (5 conditions x 5) plus 30 TLE runs (Starlink/OneWeb x high/medium/low x 5). Evaluate reactive QoS, orbit-only, radio/QoS-only and fused CA-QF against an oracle reference using 15/30/60-s horizons and whole-pass holdout.

## 3. Prior laboratory context to exploit

A prior TLE-driven 5G NTN telementoring study was executed in this research program and developed useful OAI/RFsim machinery. Historical handoff clues included:

- historical Paper-3 OAI: `/home/ran/MC/SATNAC/openairinterface5g`
- prior TLE study OAI: `/home/ran/MC/TLE-NTN-STUDY/openairinterface5g`
- prior public framework: `/home/ran/TLE-Driven-5G-NTN-Telementoring-Experiments`

These are clues, not current truth. Verify before use.

The prior study worked on TLE trace replay into OAI RFsim and issues/fixes around dynamic state replay, timing advance/Doppler consistency, real-time pacing, frozen versus propagated ephemeris behavior, connected-mode divergence, instrumentation and unattended execution.

Inspect the current prior-study Git state. Prefer the latest validated known-good commit/patch rather than reimplementing. Do not modify the completed prior-study checkout destructively. Create a dedicated CA-QF checkout such as `/home/ran/MC/PREDICTIVE-CAQF-STUDY/openairinterface5g`.

## 4. Public repository

Canonical: `https://github.com/mogfrey/Predictive-CAQF-5G-NTN-Experiments`.

Recommended local path: `$HOME/Predictive-CAQF-5G-NTN-Experiments`.

Clone/pull `main`, run `scripts/bootstrap_ran.sh`, and fill ignored `config/testbed.local.yaml` with confirmed values.

## 5. First actions — exact order

1. Read all authoritative files in `CODEX_MISSION.md`.
2. Capture host, OAI, Open5GS and network state.
3. Locate prior TLE study OAI/framework.
4. Record commits/diffs; do not clean/reset.
5. Identify latest validated TLE replay implementation and required runtime flags/config.
6. Create a separate CA-QF OAI checkout from that validated state.
7. Fill `config/testbed.local.yaml`.
8. Run `caqf-exp validate-config` and `caqf-exp preflight`.
9. Re-prove required controls.
10. Generate/freeze TLE snapshots, passes and traces.
11. Validate state fidelity.
12. Build one-run non-interactive runner/collectors.
13. Perform engineering calibration/dry runs.
14. Freeze final environment.
15. Only then execute publishable runs.

## 6. Condition IDs

Controlled: `C-GEO-FEASIBLE`, `C-GEO-OVERLOAD`, `C-STATIC-LEO-FEASIBLE`, `C-NATIVE-LEO-FEASIBLE`, `C-NATIVE-LEO-OVERLOAD`.

TLE: `T-S-HIGH`, `T-S-MEDIUM`, `T-S-LOW`, `T-O-HIGH`, `T-O-MEDIUM`, `T-O-LOW`.

Exactly five valid/relevant final repetitions per condition. Invalid lab/instrumentation/operator runs remain archived and may be replaced with documented replacement runs.

## 7. Required telemetry per run

Orbital/NTN: UTC and run time, constellation/pass/satellite ID, TLE hash/epoch, position/velocity, elevation, slant range, range rate, geometric delay, Doppler, OAI-applied/observed NTN and timing/TA state where available.

RAN/protocol: RRC/PDU state, MCS, SNR/SINR, BLER, DTX, HARQ retransmission indicators/counts, UL failure, out-of-sync/synchronization events and terminal/radio failure time where exposed.

Transport/QoS: offered rate, receiver goodput and loss at 1-s resolution, RTT, flow start/end/interruption and first persistent QoS infeasibility.

System/provenance: exact commands, config snapshots/hashes, framework/OAI commits/diffs, Open5GS version/state, clock state and run classification.

Unavailable radio metrics are recorded as unavailable, not fabricated.

## 8. Traffic/event definitions

Final workload is continuous UDP `iperf3`-class traffic with frozen offered rate. Calibration determines feasible and overload rates. Pilot defaults: goodput >=95% of offered rate, loss <=1%, two consecutive 1-s infeasible windows define persistent QoS termination. Collect RTT; if it becomes part of final `F_Q`, freeze its threshold before confirmatory runs.

## 9. Pass selection/replay

Use one frozen reputable TLE snapshot per source set, record retrieval UTC and hash, select first chronological pass satisfying each geometry band, and reuse an identical trace for all five repetitions. Do not regenerate traces between repetitions unless corruption is proven and documented.

## 10. State fidelity

Before final TLE runs, compare reference state with OAI-applied/logged state for observable position/velocity, timing/delay and Doppler. Define numeric tolerances from actual pinned OAI quantization/update semantics before freeze. Do not proceed if replay clearly controls the wrong state.

## 11. Predictor outputs

Preserve explicit fold definitions, per-snapshot predictions, event-level trigger times, misses/false triggers, warning times, calibration metrics and run-level summaries. No held-out pass leakage.

## 12. End state

Create `PREDICTIVE_CAQF_5G_NTN_FINAL_RESULTS_<YYYYMMDD>.zip` with checksum and completeness report. When complete, stop additional experiments unless the paper-analysis chat identifies a specific missing requirement.
