# Granular Experiment Operator Guide
## Predictive CA-QF over TLE-Driven 5G Release-17 NTN

### How to use this guide

Codex should drive this guide one bounded checkpoint at a time. Do not run the whole document blindly. At each checkpoint, inspect outputs, fix the current gate, then continue.

The scientific contract is authoritative. Commands are templates and may be adapted to the real host.

# 0. Completion target

Success means:

1. the existing laboratory is preserved;
2. a dedicated CA-QF OAI study checkout is pinned;
3. the public framework is installed and committed;
4. controlled GEO/static-LEO/native-LEO states are validated;
5. Starlink/OneWeb TLE inputs and six geometry-selected passes are frozen;
6. TLE-derived state is faithfully replayed/propagated into the Release-17 OAI NTN path;
7. synchronized orbital/RAN/transport telemetry is collected;
8. feasible/overload service rates and QoS definitions are frozen;
9. all 55 publishable runs are complete with run-level provenance;
10. whole-pass-holdout processed features/predictions are generated;
11. all failures/invalid runs are classified;
12. one final ZIP passes completeness and checksum validation.

Final ZIP:

`PREDICTIVE_CAQF_5G_NTN_FINAL_RESULTS_<YYYYMMDD>.zip`

# 1. Phase A — preserve the current laboratory

Before upgrades or edits:

```bash
mkdir -p ~/caqf_lab_snapshot
date -u +"%Y-%m-%dT%H:%M:%SZ" | tee ~/caqf_lab_snapshot/snapshot_time_utc.txt
hostnamectl | tee ~/caqf_lab_snapshot/hostnamectl.txt
uname -a | tee ~/caqf_lab_snapshot/uname.txt
cat /etc/os-release | tee ~/caqf_lab_snapshot/os-release.txt
ip -br addr | tee ~/caqf_lab_snapshot/ip_br_addr.txt
ip route | tee ~/caqf_lab_snapshot/ip_route.txt
ps -eo pid,lstart,cmd | grep -E 'nr-softmodem|nr-uesoftmodem|open5gs' | grep -v grep | tee ~/caqf_lab_snapshot/processes.txt || true
```

If available:

```bash
chronyc tracking | tee ~/caqf_lab_snapshot/chrony_tracking.txt
```

Checkpoint A: identify RAN/core topology and confirm no destructive change was made.

# 2. Phase B — locate prior OAI environments

Search narrowly:

```bash
find "$HOME" /opt /usr/local -maxdepth 5 -type d -name openairinterface5g 2>/dev/null
```

For every plausible checkout:

```bash
cd <OAI_ROOT>
git remote -v
git branch --show-current
git rev-parse HEAD
git describe --tags --always --dirty
git status --short
git diff --stat
```

Capture dirty diffs before editing:

```bash
git diff > ~/caqf_lab_snapshot/<NAME>_OAI_PREEXISTING.patch
```

Specifically look for the prior TLE-driven study checkout and inspect its commits/patches relating to RFsim trace replay, NTN ephemeris, timing advance, Doppler, pacing and freeze-ephemeris behavior.

Checkpoint B: identify the latest previously validated TLE/OAI state to reuse.

# 3. Phase C — create a dedicated CA-QF OAI checkout

Do not modify the completed previous study in place.

Prefer a separate checkout such as:

`/home/ran/MC/PREDICTIVE-CAQF-STUDY/openairinterface5g`

Create it from the validated source commit/branch chosen at Checkpoint B. Record exact ancestry and any cherry-picked patches.

Checkpoint C: dedicated checkout exists, builds, and prior study remains recoverable.

# 4. Phase D — clone/install this public framework

```bash
cd "$HOME"
git clone https://github.com/mogfrey/Predictive-CAQF-5G-NTN-Experiments.git
cd Predictive-CAQF-5G-NTN-Experiments
bash scripts/bootstrap_ran.sh "$PWD"
```

If already cloned:

```bash
cd "$HOME/Predictive-CAQF-5G-NTN-Experiments"
git status --short
git pull --ff-only
bash scripts/bootstrap_ran.sh "$PWD"
```

Copy local template:

```bash
cp config/testbed.example.yaml config/testbed.local.yaml
```

Fill only confirmed host values. Never commit subscriber secrets.

Run:

```bash
caqf-exp validate-config --campaign config/campaign.yaml
caqf-exp preflight --testbed config/testbed.local.yaml
```

Checkpoint D: both pass.

# 5. Phase E — discover/prove Open5GS and network readiness

Record deployment/version and prove the existing UE can establish a PDU session in a known-good control state. Reuse working prior commands where possible.

Capture core host/version/deployment, UE tunnel/interface, UE IP, iperf endpoint reachability and relevant routing. Do not redesign the core unless a concrete blocker requires it.

Checkpoint E: RRC/PDU/IP path works in a known-good control state.

# 6. Phase F — prove the required NTN engineering profiles

Before final data, prove engineering candidates for:

1. GEO feasible;
2. GEO overload;
3. static LEO feasible;
4. native dynamic LEO feasible;
5. native dynamic LEO overload.

Engineering trials may be exploratory. They are not final repetitions.

Record exact gNB/UE commands and config sources. Ensure static LEO truly holds orbital state static and native LEO truly uses the pinned OAI native dynamic mechanism.

Checkpoint F: the five Block-A condition meanings can be created reproducibly.

# 7. Phase G — calibrate and freeze traffic rates

Use UDP receiver-side reporting at 1-s resolution.

Choose:

- `feasible_rate_mbps`: comfortably satisfies goodput/loss requirements under stable reference conditions;
- `overload_rate_mbps`: reliably violates transport feasibility under the intended overload controls.

Do not choose final rates by looking for aesthetically favorable CA-QF outcomes.

Update `config/campaign.yaml`, set the rate values, change the status from provisional engineering calibration to frozen, commit, and hash the file.

Checkpoint G: final traffic rates are frozen before confirmatory runs.

# 8. Phase H — obtain and freeze TLE snapshots

Use a reputable public TLE source and verify the current source before downloading.

```bash
mkdir -p data/tle results/engineering/tle
```

After retrieval:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ" > data/tle/retrieval_time_utc.txt
sha256sum data/tle/* | tee data/tle/SHA256SUMS.txt
```

Record source metadata and TLE epochs. Do not fetch a fresh TLE for each repetition.

Checkpoint H: immutable TLE inputs exist and are hashed.

# 9. Phase I — geometry-select six passes

Use the observer coordinates and frozen TLE snapshot.

Example:

```bash
caqf-exp select-passes \
  --campaign config/campaign.yaml \
  --tle-file data/tle/<STARLINK_TLE> \
  --start <START_UTC> \
  --horizon-hours 48 \
  --lat <LAT> --lon <LON> --alt-m <ALT_M> \
  --carrier-hz <NR_CARRIER_HZ> \
  --output results/engineering/tle/starlink_selected_passes.json
```

Repeat for OneWeb.

The first chronological pass satisfying each high/medium/low band is selected. If missing, extend the search horizon before inspecting network outcomes.

Freeze and hash the selected-pass JSONs.

Checkpoint I: exactly six pass IDs are frozen.

# 10. Phase J — generate deterministic orbital traces

For each selected pass, generate a 1-s trace covering the intended visibility/experiment interval.

```bash
caqf-exp tle-trace \
  --tle-file data/tle/<TLE_FILE> \
  --satellite <SATELLITE> \
  --start <TRACE_START_UTC> \
  --duration-s <DURATION> \
  --step-s 1 \
  --lat <LAT> --lon <LON> --alt-m <ALT_M> \
  --carrier-hz <NR_CARRIER_HZ> \
  --output results/engineering/tle/<PASS_ID>_trace.csv
```

Hash every trace. Five repetitions of a pass must reuse that exact file.

Checkpoint J: six deterministic traces exist and hashes are frozen.

# 11. Phase K — integrate TLE state into OAI

This is the central engineering step.

Prefer reuse of the prior validated TLE-driven OAI replay mechanism. Codex may patch the dedicated CA-QF OAI checkout and public scripts as needed.

Required outcome: frozen trace/epoch state controls the intended Release-17 NTN position/velocity/timing/Doppler behavior. It must not collapse into arbitrary `tc/netem` impairment playback.

Verify source semantics and units on the pinned OAI checkout before mapping fields.

Checkpoint K: one TLE engineering condition reaches stable RRC/PDU/IP and follows the intended orbital state.

# 12. Phase L — TLE state-fidelity validation

For one Starlink and one OneWeb representative trace, preserve target reference trace, OAI-applied/logged state where observable, timestamp alignment, position/velocity error where comparable, delay/timing error where comparable, Doppler error where comparable, raw gNB/UE logs and a fidelity summary.

Define tolerances from pinned OAI quantization/update semantics and record them before final runs.

Checkpoint L: fidelity is scientifically credible and repeatable.

# 13. Phase M — build synchronized collectors

Every final run directory must contain, at minimum:

```text
results/final/<CONDITION>/run_<N>_<UTC>/
  manifest.json
  run_status.json
  config_snapshot/
  orbital/reference_trace.csv
  orbital/applied_state.csv          # where available
  oai/gnb.log
  oai/ue.log
  network/rtt.csv
  transport/iperf.json
  transport/intervals.csv
  clocks/before.txt
  clocks/after.txt
```

Normalized time-aligned metrics must preserve the fields in `schemas/time_aligned_metrics.csv` where available.

All streams use UTC plus run-relative `t_s`. Do not align by eyeballing plots.

Checkpoint M: one dry run produces a complete, parseable directory.

# 14. Phase N — implement QoS/event parser

At 1-s resolution derive offered rate, receiver goodput, loss fraction, RTT, `qos_feasible`, first persistent QoS termination, gNB/UE radio-failure event times and out-of-sync events.

Default QoS feasibility from frozen config:

- goodput >= 0.95 x requested/offered rate;
- loss <= 0.01;
- persistent termination = two consecutive infeasible windows.

If RTT becomes part of `F_Q`, freeze that threshold before final runs.

Checkpoint N: event extraction agrees with manual inspection on dry-run logs.

# 15. Phase O — build a non-interactive one-run command

Create a command such as:

```bash
caqf-run-one --condition C-GEO-FEASIBLE --repeat 1
```

It must automate the lifecycle and return safely. Condition-induced NTN failure is a valid experimental result and should not make the runner retry automatically.

Run status values:

- `valid_success`
- `condition_induced_failure`
- `invalid_lab_failure`
- `operator_error`
- `instrumentation_failure`

Never delete invalid runs.

Checkpoint O: one-run command works for controlled and TLE conditions.

# 16. Phase P — mandatory dry runs

Before final freeze, execute exactly one engineering/dry run of each condition class:

- GEO feasible;
- GEO overload;
- static LEO feasible;
- native LEO feasible;
- native LEO overload;
- one Starlink TLE pass;
- one OneWeb TLE pass.

Inspect all collectors and parsers. Fix instrumentation now, not midway through the final campaign.

Checkpoint P: all seven dry-run classes pass instrumentation QC.

# 17. Phase Q — freeze the final environment

Create:

```bash
mkdir -p results/freeze
```

Record framework commit/dirty state, OAI commit/dirty state/diff, Open5GS version, OS/kernel, config hashes, TLE hashes, trace hashes, selected-pass JSON hashes, traffic/QoS config, predictor config and pass-fidelity tolerances.

Preferred state is clean committed code/config, excluding private local config.

Generate campaign plan:

```bash
python scripts/make_campaign_plan.py
```

Confirm it contains 55 condition/repetition rows.

Checkpoint Q: final freeze is complete and immutable for the campaign.

# 18. Phase R — execute the final 55-run campaign

Use Linux/tmux/watchdog rather than keeping Codex waiting.

Example:

```bash
tmux new -s caqf_campaign
bash scripts/campaign_watchdog.sh
```

Codex should leave the long-running process to Linux and return only when status/QC needs review.

After every five-run condition, pause and run batch QC. Confirm same config/OAI/framework/trace hashes and complete major logs.

Do not continue past a batch QC failure.

# 19. Phase S — failure handling

Condition-induced failure is data. Preserve it.

Invalid lab/instrumentation/operator failure remains in the archive and may receive a replacement run. Record replacement linkage. Never silently overwrite run numbers or delete the failed directory.

If a software/config change is required after final runs have started, determine whether it changes experimental comparability. If yes, stop and flag a methodology/freeze break rather than mixing incompatible data.

# 20. Phase T — normalized processing

Generate one time-aligned table per run and a combined table.

Then:

```bash
caqf-exp features \
  --campaign config/campaign.yaml \
  --predictor config/predictor.yaml \
  --input results/processed/time_aligned_metrics.csv \
  --output results/processed/feature_snapshots.csv
```

The feature builder must be causal. Rolling features use current/past samples only.

# 21. Phase U — predictive evaluation

Primary split: whole-pass holdout.

Reference command:

```bash
caqf-exp evaluate \
  --campaign config/campaign.yaml \
  --input results/processed/feature_snapshots.csv \
  --output-dir results/processed/evaluation
```

Codex may improve the reference evaluator, but must save explicit fold definitions proving no pass overlap.

Required predictor families: reactive QoS, orbit-only, radio/QoS-only, fused CA-QF and oracle reference. Required horizons: 15/30/60 s. Also perform constellation-transfer evaluation after primary folds.

# 22. Phase V — run-level/event-level statistics

Produce machine-readable summaries including run counts/status, event counts, pre-failure trigger coverage, missed events, false/unnecessary mobility-preparation triggers, warning time per event/run, Brier/calibration metrics, predictor comparison by `T_req`, pass/constellation-stratified summaries and run-level confidence intervals where meaningful.

Do not treat 1-s prediction snapshots as independent experiment replicates.

# 23. Phase W — final results structure

Create:

```text
FINAL_RESULTS/
├── 00_HANDOFF/
│   ├── HANDOFF_SUMMARY.md
│   ├── CAMPAIGN_COMPLETENESS.md
│   ├── run_index.csv
│   ├── invalid_runs.csv
│   └── deviations_from_plan.md
├── 01_ENVIRONMENT/
│   ├── host_inventory/
│   ├── oai_version/
│   ├── open5gs_version/
│   └── clock_sync/
├── 02_CODE_SNAPSHOT/
│   ├── experiment_repo_commit.txt
│   ├── experiment_repo_diff.patch
│   ├── oai_commit.txt
│   └── oai_local_diff.patch
├── 03_CONFIG_FREEZE/
│   ├── sanitized_configs/
│   ├── private_config_hashes.txt
│   └── SHA256SUMS.txt
├── 04_ORBITAL_INPUTS/
│   ├── tle_snapshots/
│   ├── source_metadata/
│   ├── selected_passes/
│   ├── generated_traces/
│   └── SHA256SUMS.txt
├── 05_ENGINEERING_VALIDATION/
│   ├── controls/
│   ├── tle_state_fidelity/
│   └── dry_runs/
├── 06_CONTROLLED_RUNS/
│   ├── C-GEO-FEASIBLE/
│   ├── C-GEO-OVERLOAD/
│   ├── C-STATIC-LEO-FEASIBLE/
│   ├── C-NATIVE-LEO-FEASIBLE/
│   └── C-NATIVE-LEO-OVERLOAD/
├── 07_TLE_PREDICTIVE_RUNS/
│   ├── T-S-HIGH/
│   ├── T-S-MEDIUM/
│   ├── T-S-LOW/
│   ├── T-O-HIGH/
│   ├── T-O-MEDIUM/
│   └── T-O-LOW/
├── 08_PROCESSED/
│   ├── run_level_metrics.csv
│   ├── time_aligned_metrics.csv
│   ├── feature_snapshots.csv
│   ├── event_summary.csv
│   ├── predictions.csv
│   ├── fold_definitions.csv
│   ├── predictor_summary.csv
│   └── constellation_transfer_summary.csv
├── 09_QC/
│   ├── completeness_report.json
│   ├── hash_validation.txt
│   └── notes.md
└── 10_MODELS/
    ├── model_metadata/
    └── calibration/
```

# 24. Phase X — required run index

At minimum:

```text
run_id
condition_id
block
constellation
pass_id
pass_band
satellite_id
repetition
status
replacement_for
start_utc
end_utc
framework_commit
oai_commit
config_hash
tle_hash
trace_hash
offered_rate_mbps
notes
```

# 25. Phase Y — sanitize and checksum

Scan the final package for credentials/private values. Keep scientific metrics; sanitize only sensitive values.

Then from `FINAL_RESULTS`:

```bash
find . -type f ! -name 'SHA256_ALL_FILES.txt' -print0 | sort -z | xargs -0 sha256sum > SHA256_ALL_FILES.txt
sha256sum -c SHA256_ALL_FILES.txt | tee 09_QC/hash_validation.txt
```

No unexplained checksum failure is acceptable.

# 26. Phase Z — final completeness gate

Before completion, verify:

- [ ] C-GEO-FEASIBLE: 5 valid/relevant final reps
- [ ] C-GEO-OVERLOAD: 5
- [ ] C-STATIC-LEO-FEASIBLE: 5
- [ ] C-NATIVE-LEO-FEASIBLE: 5
- [ ] C-NATIVE-LEO-OVERLOAD: 5
- [ ] T-S-HIGH: 5
- [ ] T-S-MEDIUM: 5
- [ ] T-S-LOW: 5
- [ ] T-O-HIGH: 5
- [ ] T-O-MEDIUM: 5
- [ ] T-O-LOW: 5
- [ ] all invalid/replacement runs listed
- [ ] all six passes selected before network outcomes and frozen
- [ ] all TLEs/traces/configs hashed
- [ ] TLE state fidelity validation complete
- [ ] feasible/overload rates frozen before final campaign
- [ ] exact framework/OAI/Open5GS versions captured
- [ ] whole-pass holdout demonstrated with fold definitions
- [ ] 15/30/60-s evaluations complete
- [ ] reactive/orbit-only/radio-QoS/fused/oracle outputs complete
- [ ] false-trigger/miss/warning/calibration outputs complete
- [ ] constellation-transfer tests complete or explicitly documented infeasible
- [ ] raw logs retained
- [ ] no silent methodology changes
- [ ] final checksums pass
- [ ] final ZIP created and hashed
- [ ] no secrets included

Create:

```bash
DATE_UTC=$(date -u +%Y%m%d)
ZIP_NAME="PREDICTIVE_CAQF_5G_NTN_FINAL_RESULTS_${DATE_UTC}.zip"
zip -r -9 "$ZIP_NAME" FINAL_RESULTS
sha256sum "$ZIP_NAME" | tee "${ZIP_NAME}.sha256"
```

When and only when all mandatory items pass, report:

**EXPERIMENT CAMPAIGN COMPLETE. Stop running experiments. Attach the final ZIP to the paper-analysis chat.**

# 27. Troubleshooting rule

When something fails: stop at the current gate; preserve evidence; collect the smallest useful diagnostic; make the smallest safe engineering change; rerun one engineering validation; document the material change; continue only when the gate passes.

Codex owns engineering execution. It does not own the scientific objective.
