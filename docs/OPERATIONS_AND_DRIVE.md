# Operations, Dashboard, Watchdog, and Progressive Drive Handoff

This file defines the non-scientific operations layer for unattended execution. The scientific contract remains authoritative.

## Runtime location

Codex should install the live operations workspace outside the research repository at:

`$HOME/codex-caqf/`

Recommended runtime tree:

```text
codex-caqf/
├── dashboard/
├── watchdog/
├── state/
├── logs/
├── recovery/
└── drive_stage/
```

The repository contains source/templates under `ops/`; runtime state must not be committed.

## Dashboard requirements

The dashboard must show at minimum:

- total campaign progress out of 55 publishable runs;
- current phase, condition, repetition and run ID;
- valid / invalid / failed run counts;
- current-run elapsed time and best available ETA;
- campaign-controller health;
- gNB / UE / Open5GS / PDU-session health where observable;
- orbital replay/trace identity and state-fidelity status;
- telemetry/collector health;
- Google Drive handoff health and last successful upload;
- **watchdog health**, including state, last heartbeat, last repair attempt, repeated-failure count and whether automatic Codex recovery is armed;
- final freeze/QC/READY state.

The dashboard is observational only. It must not alter experiment state.

### Dashboard URL discovery and persistence

The operator must not have to discover the dashboard address manually. When the dashboard is first validated, Codex must:

1. choose a host/port that is reachable from the operator's normal management network without changing firewall/security policy unless necessary;
2. determine the appropriate RAN-host address and exact dashboard URL;
3. write the exact URL as a single line to `$HOME/codex-caqf/state/dashboard_url.txt`;
4. print a highly visible terminal line exactly in the form `CAQF_DASHBOARD_URL=<url>` before proceeding to the next major phase;
5. keep `dashboard_url.txt` current if the address or port changes;
6. include the URL in `$HOME/codex-caqf/state/dashboard_snapshot.json` and the final completion report.

Do not publish host addresses or other private infrastructure details to the public GitHub repository.

## Watchdog requirements

The watchdog must be independent from the campaign controller so a dead controller cannot report itself healthy. It writes `$HOME/codex-caqf/state/watchdog_health.json` on every cycle.

Required watchdog states:

`HEALTHY`, `RUNNING`, `EXPECTED_CONDITION_FAILURE`, `INFRASTRUCTURE_FAILURE`, `INSTRUMENTATION_FAILURE`, `CONTROLLER_DEAD`, `STALLED`, `NEEDS_CODEX`, `RECOVERING`, `PAUSED`, `COMPLETE`.

A scientific/condition-induced failure is data, not an engineering fault. The watchdog must never erase or silently rerun such a run.

For recoverable engineering faults it should:

1. preserve the failed run and all logs;
2. create a compact recovery packet;
3. hash/classify the failure signature;
4. invoke a fresh headless Codex repair session only if automatic recovery is enabled;
5. require the repair prompt to preserve all scientific invariants;
6. run the smallest engineering validation appropriate to the fault;
7. resume from the last valid campaign checkpoint only when safe.

Bounded recovery is mandatory. Default maximum: 3 Codex repair attempts for the same failure signature. After that, set `PAUSED` and stop burning credits.

Codex must verify the installed Codex CLI syntax before arming automatic recovery and record the exact command in `$HOME/codex-caqf/state/codex_recovery_command.txt`. Do not hard-code credentials or auth material.

## Progressive Google Drive handoff

The previous study used an authenticated `rclone` remote named `gdrive`. Codex must discover and test the existing remote without exposing its OAuth configuration. If the remote is unavailable, repair/re-authenticate only if this can be done without revealing secrets; otherwise pause and report the blocker.

For this campaign use a new destination root:

`gdrive:PREDICTIVE_CAQF_ANALYSIS_HANDOFF`

Recommended structure:

```text
PREDICTIVE_CAQF_ANALYSIS_HANDOFF/
├── 00_status/
├── 01_controlled/
├── 02_starlink/
├── 03_oneweb/
├── 04_predictive_analysis/
└── 99_final/
```

The handoff is allow-list/sanitization based. Never upload subscriber credentials, IMSI/K/OP/OPc, SSH keys, passwords, tokens, rclone config, private UE configs or unsanitized secrets.

### Incremental cadence

Upload sanitized operational status to `00_status/` after every completed or classified run and whenever a watchdog state changes materially. At minimum publish:

- `campaign_status.json`
- `run_index.csv`
- `watchdog_health.json`
- `dashboard_snapshot.json`
- `drive_health.json`
- current QC/failure summary when available.

For each completed phase, upload in this order:

1. sanitized unpacked CSV/JSON/Markdown analysis files;
2. phase ZIP;
3. phase ZIP SHA256;
4. `PHASE_X_READY.txt` **last**.

The READY marker is the atomic external-analysis gate. A phase is not safe for manuscript analysis until its marker exists.

Suggested phase bundles:

- `PHASE_A_CONTROLLED_ANALYSIS.zip`
- `PHASE_B_STARLINK_ANALYSIS.zip`
- `PHASE_C_ONEWEB_ANALYSIS.zip`
- `PHASE_D_PREDICTIVE_ANALYSIS.zip`

Final package:

`PREDICTIVE_CAQF_5G_NTN_FINAL_RESULTS_<YYYYMMDD>.zip`

Upload the final ZIP, SHA256, then `FINAL_READY.txt` last.

## Drive failure semantics

Drive/reporting failure does not invalidate an otherwise valid scientific run. Preserve local results, mark Drive degraded on the dashboard, retry uploads independently, and never rerun a valid network experiment merely because Drive failed.

## Start gate

No publishable campaign may begin until Codex has demonstrated:

- dashboard is live and correctly reports watchdog health;
- `$HOME/codex-caqf/state/dashboard_url.txt` exists and the URL has been printed to the operator;
- watchdog independently detects a deliberately stopped test controller;
- watchdog bounded-recovery logic is tested with a harmless synthetic fault;
- Drive upload/read-back test passes;
- dashboard shows Drive and watchdog status accurately;
- all existing scientific engineering/freeze gates pass.
