# CODEX_MISSION.md
## Predictive CA-QF 5G NTN — Autonomous Laboratory Mission

### Read first

Read `docs/SCIENTIFIC_CONTRACT.md`, `docs/CODEX_EXECUTION_HANDOFF.md`, `docs/EXPERIMENT_OPERATOR_GUIDE.md`, `docs/OPERATIONS_AND_DRIVE.md`, and `config/campaign.yaml` completely before editing or running the laboratory.

The scientific contract is authoritative when engineering convenience conflicts with experimental meaning.

## 1. Ultimate objective

Build and execute the approved 55-run confirmatory campaign that tests whether predictive CA-QF can causally distinguish current transport infeasibility from approaching continuity loss and provide useful pre-failure mobility-preparation warning across controlled and TLE-driven Release-17 NTN conditions.

Primary chain: `service demand -> TLE/SGP4 + observable RAN/QoS state -> Release-17 OAI NTN -> transport -> causal viability probability -> CONTINUE / PREPARE_MOBILITY / QOS_INFEASIBLE`.

## 2. Codex reasons, Linux executes

Use Codex for diagnosis, code changes, validation decisions and scientific-contract checks. Use Linux/tmux/shell scripts for long waits and repeated runs. Do not keep Codex consuming usage while a 5–10 minute experiment is simply running; build unattended controller/watchdog processes, launch them independently, and return to Codex only for engineering work or bounded recovery.

The operator wants a hands-off workflow. Do ordinary host setup, discovery, cloning, configuration, validation, dashboard/watchdog installation and campaign orchestration yourself instead of asking the operator to execute routine commands.

## 3. Preserve and reuse prior validated work

A recently completed TLE-driven OAI NTN study may already exist on the same research host. The host may contain a historical Paper-3 OAI checkout, a separate TLE-study OAI checkout, a public telementoring experiment repository and a proven Open5GS setup.

Do not assume paths are unchanged. Discover narrowly and capture exact commits/diffs. If a validated prior TLE/OAI integration exists, reuse it through a separate CA-QF checkout or branch. Do not destructively modify the completed prior-study checkout.

## 4. Mandatory preservation before first edit

Capture host/kernel/network summary, running gNB/UE/core commands, OAI paths/commits/dirty diffs, Open5GS deployment/version, clock state and prior public framework commit. Preserve any uncommitted OAI patch before modifying it.

## 5. Engineering gates before final campaign

Do not start publishable runs until all applicable gates pass: framework install/config validation; dedicated OAI checkout; stable core/PDU/IP path; GEO/static/native LEO controls; frozen TLEs/passes/traces; state-fidelity validation; synchronized collectors; calibrated and frozen traffic rates; dry-run instrumentation; final software/config/input freeze; unattended controller; independently healthy watchdog; live dashboard; progressive Drive handoff read-back test.

## 6. OAI strategy

Prefer the fastest scientifically sound path. Reuse the latest validated prior TLE replay state if available. Preserve prior-study artifacts. Avoid upgrading to a fresh OAI release unless a concrete blocker requires it. Record every OAI patch used for final runs.

Prior fixes may involve RFsim state replay, timing advance/Doppler consistency, real-time pacing, frozen/propagated ephemeris behavior and connected-mode state divergence. Inspect and reuse rather than rediscovering blindly.

## 7. Traffic calibration

Engineering calibration may probe rates, but final feasible and overload rates must be fixed before confirmatory outcomes are inspected. Feasible load should have stable margin; overload should reliably violate transport feasibility without requiring an orbital continuity event.

## 8. Required unattended runner

Build a non-interactive command such as `caqf-run-one --condition <ID> --repeat <N>` that snapshots provenance, starts the correct gNB/UE state, waits for RRC/PDU/IP readiness, starts collectors, runs frozen UDP traffic, preserves orbital/RAN/transport telemetry, stops cleanly, classifies status, retains failed runs, returns nonzero on invalid-lab/instrumentation failure, and treats condition-induced link failure as data rather than a runner failure.

The campaign controller must emit machine-readable PID, heartbeat, current-run, campaign-status and fault state under `$HOME/codex-caqf/state/` or an equivalent documented runtime path so an independent watchdog can supervise it.

## 9. Watchdog and self-correction

Install the runtime operations workspace outside the scientific repository at `$HOME/codex-caqf/` using `scripts/install_ops.sh` or an improved equivalent.

The watchdog must be an independent process. It must detect controller death/stall, infrastructure faults and instrumentation faults; preserve runs; classify failures; create a compact recovery packet; and optionally launch a fresh headless Codex repair session. It must never treat a real condition-induced network failure as an engineering failure.

Automatic recovery is bounded: at most 3 Codex repair attempts for the same failure signature by default. After the limit, pause safely. Before arming recovery, inspect the locally installed Codex CLI and record a tested headless recovery command in `$HOME/codex-caqf/state/codex_recovery_command.txt`. Do not guess syntax or embed credentials.

The recovery session may fix engineering implementation but may not alter the scientific contract, frozen inputs, repetitions, selected passes, QoS thresholds, horizons, predictor split rules or post-freeze traffic rates.

## 10. Dashboard

Provide an HTML dashboard that reads machine-readable runtime state without mutating experiments. It must show total progress, phase/condition/repetition/run ID, ETA, controller/RAN/core/PDU health, orbital replay/state-fidelity status, telemetry health, Drive handoff status, and **watchdog health** including heartbeat, state, recovery-armed status, repair attempts and latest failure signature.

Before final runs, prove the dashboard correctly changes watchdog state when a harmless test controller is stopped/stalled.

## 11. Progressive Google Drive handoff

The prior study used an authenticated `rclone` remote named `gdrive`; discover and verify it without exposing its OAuth configuration. For this campaign create/use `gdrive:PREDICTIVE_CAQF_ANALYSIS_HANDOFF` with `00_status`, controlled, Starlink, OneWeb, predictive-analysis and final areas as specified in `docs/OPERATIONS_AND_DRIVE.md`.

After every completed or classified run, incrementally upload sanitized status/run-index/watchdog/dashboard/Drive-health summaries to `00_status/`. At each phase completion, upload unpacked sanitized analysis, phase ZIP, SHA256, then the phase READY marker last. Upload the final ZIP/checksum and `FINAL_READY.txt` last.

Drive/reporting failure does not invalidate a valid scientific run and must never trigger rerunning that run. Preserve locally and retry Drive independently.

## 12. Failure protocol

Unexpected failure: stop or pause the unattended campaign; preserve logs; classify failure; diagnose narrowly; make the smallest safe fix; perform one engineering validation; determine whether prior final runs remain comparable; document the change; resume only when safe.

## 13. Predictor/evaluation discipline

The novelty is not an ML algorithm. The repository includes a reference probabilistic evaluator. Codex may improve it, including a discrete-time survival model, while preserving causal feature construction, whole-pass grouping, no scaler/imputer leakage, required feature ablations, 15/30/60-s horizons and event-level false-trigger/miss/warning metrics. Do not optimize on held-out pass outcomes.

## 14. Priority order

P0 preserve/reuse the validated prior OAI/TLE integration safely. P1 install/prove dashboard, watchdog and Drive handoff. P2 complete one TLE-driven CA-QF engineering run end-to-end with full telemetry. P3 freeze campaign inputs and prove unattended execution. P4 execute 55 publishable runs with batch QC and incremental Drive handoffs. P5 generate processed features/predictions/statistics and the final results package.

Avoid spending time on cosmetic plotting or manuscript writing on the RAN host.

## 15. Security

Never expose or commit UE subscriber keys/OP/OPc, credentials/tokens, private host access secrets, rclone OAuth configuration or unsanitized private infrastructure configs.

## 16. Completion rule

Complete only when the operator-guide completeness gate passes, `PREDICTIVE_CAQF_5G_NTN_FINAL_RESULTS_<YYYYMMDD>.zip` exists with a checksum, the final package is uploaded, `FINAL_READY.txt` is verified on Drive, and the dashboard/watchdog report COMPLETE. Then stop experiments and leave a concise handoff for the paper-analysis chat.
