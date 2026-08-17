# Scientific Contract — Predictive CA-QF 5G NTN Experiments

## Status

This document freezes the scientific meaning of the confirmatory campaign. Engineering implementation may evolve. The items explicitly marked non-negotiable may not change silently.

## 1. Central thesis

A 5G NTN serving-link decision should not rely on current QoS alone. It should also estimate, with uncertainty, whether the requested QoS is likely to remain feasible for long enough to safely continue service or prepare mobility.

For decision time `t`, service horizon `T_req`, and causally available observations `X_t`, the operational continuity quantity is `P(T_rem >= T_req | X_t)`.

## 2. Approved research questions

### RQ1 — Distinct failure modes
Can transport infeasibility and continuity risk be experimentally distinguished: a link that cannot satisfy QoS now versus a link that satisfies QoS now but will lose support soon?

### RQ2 — Causal prediction
Using only information available at or before decision time `t`, can remaining QoS-support viability be predicted from orbital state, radio state and recent transport observations?

### RQ3 — Decision advantage
Does predictive CA-QF provide materially earlier useful warning than reactive QoS triggering without producing excessive unnecessary mobility preparation?

### RQ4 — Orbital generalization
Does the predictive decision remain useful across multiple geometry-selected passes and representative Starlink and OneWeb TLE-derived orbital conditions rather than only one repeatable RFsim cycle?

## 3. Approved decision semantics

- `CONTINUE`: current QoS is feasible and predicted continuity confidence is sufficient.
- `PREPARE_MOBILITY`: current QoS is feasible but continuity confidence is insufficient for the requested horizon.
- `QOS_INFEASIBLE`: requested QoS is already not being met.

The framework must preserve causes rather than hiding them behind an opaque binary product.

## 4. Non-negotiable scientific rules

1. Primary dynamic chain: `TLE/SGP4 -> orbital state -> Release-17 NTN state -> OAI behavior -> transport QoS -> predictive CA-QF`.
2. Arbitrary dynamic `tc/netem` impairment profiles must not become the claimed orbital model.
3. Five independent repetitions are required for every publishable confirmatory condition.
4. The run is the statistical unit; packets, 1-s windows, HARQ events and prediction snapshots are not independent experimental replicates.
5. The approved confirmatory campaign contains exactly 55 publishable runs: 25 controlled + 30 TLE-driven.
6. TLE snapshots and generated traces are frozen, hashed, archived and replayable.
7. Pass selection is determined by orbital geometry before network/QoS outcomes are inspected.
8. Repetitions of the same pass reuse exactly the same frozen orbital trace.
9. Failed runs are retained and classified. Do not rerun until a desirable outcome is obtained.
10. Final QoS thresholds, traffic rates, software versions and probability operating points are frozen before confirmatory outcomes are inspected.
11. The held-out unit for predictive validation is the entire orbital pass. Repetitions of a held-out pass may not appear in training, calibration, normalization or hyperparameter selection.
12. A held-out prediction may not use future held-out radio or transport telemetry.
13. Any deterministic future orbital geometry used by an operational predictor must be derivable from the already-frozen TLE/SGP4 model and contain no network outcome information.
14. The retrospective oracle uses complete outcomes only as ground truth/upper-bound reference, not as an operational competitor.
15. Exact OAI, Open5GS, framework, TLE, trace and configuration versions/hashes must be captured per run.
16. OAI/RFsim host wall-clock timing must not be mislabeled physical satellite propagation time.
17. This is not operational Starlink/OneWeb service measurement; constellation TLEs provide geometry to a controlled OAI NTN experiment.
18. No genuine handover is claimed unless a real supported satellite/cell transition is exercised. `PREPARE_MOBILITY` is a trigger, not proof of handover.
19. No threshold or model may be tuned on held-out confirmatory pass outcomes.
20. Material deviations are retained in `deviations_from_plan.md`; they are never silently normalized away.

If an engineering limitation makes a rule impossible, stop final execution and flag `METHODOLOGY CHANGE REQUIRED`.

## 5. Confirmatory campaign

### Block A — Controlled mechanism validation, 25 runs
Five repetitions each of:

- `C-GEO-FEASIBLE`: stable reference; intended current QoS feasible and continuity stable.
- `C-GEO-OVERLOAD`: transport-infeasible reference without intended orbital continuity loss.
- `C-STATIC-LEO-FEASIBLE`: LEO-like NTN state without orbital evolution.
- `C-NATIVE-LEO-FEASIBLE`: dynamic OAI native LEO continuity reference.
- `C-NATIVE-LEO-OVERLOAD`: dynamic NTN plus transport overload.

Exact feasible and overload offered rates are selected during engineering calibration and frozen before final runs.

### Block B — TLE-driven predictive validation, 30 runs
Five repetitions each of Starlink high/medium/low and OneWeb high/medium/low passes.

Default geometry bands: high >=75 degrees, medium 40–60 degrees, low 20–30 degrees, 10-degree elevation mask, initial 48-hour search, first chronological matching pass.

If a band is unavailable, adjust search horizon/band transparently before inspecting network outcomes and record the deviation.

## 6. Predictors and baselines

Required operational comparisons:

1. `reactive_qos`: current QoS only; no predictive warning.
2. `orbit_only`: orbital/geometry state only.
3. `radio_qos_only`: RAN plus recent transport/QoS history; no orbital features.
4. `fused_caqf`: orbital + RAN + recent transport/QoS state.
5. `oracle`: retrospective reference only.

The model implementation is not the claimed novelty. Codex may improve it if causality, split discipline, feature-family boundaries and pre-freeze rules are preserved.

## 7. Required horizons

Evaluate `T_req = 15, 30, 60 s` from the same runs. Do not rerun radio experiments separately for each horizon.

## 8. Causally available features

Potential orbital features: elevation, slant range, range rate, geometric delay, Doppler, position/velocity and causally derivable pass phase.

Potential RAN features where exposed by the pinned OAI build: BLER, DTX, HARQ retransmission behavior, MCS, SNR/SINR, timing/TA state, synchronization/out-of-sync and uplink-failure indicators.

Transport/QoS features: receiver goodput, loss, RTT and rolling levels/trends.

Unavailable fields must be recorded as unavailable rather than fabricated.

## 9. QoS feasibility

Pilot-study defaults are goodput >=95% of requested/offered rate and loss <=1%. RTT must be collected. Whether RTT becomes part of empirical `F_Q` is frozen before final runs after engineering validation establishes that the measurement has the intended meaning.

Persistent QoS termination currently uses two consecutive 1-s infeasible windows as configured in `config/campaign.yaml` unless an approved pre-freeze methodology change is made.

## 10. Predictive validation discipline

Primary evaluation is leave-one-pass-out across the six TLE pass groups. For each fold, all five repetitions of the held-out pass are excluded from training/calibration, scalers/imputers are fitted on training groups only, and no future held-out network outcome is visible.

Secondary tests: train Starlink -> test OneWeb, and train OneWeb -> test Starlink.

## 11. Required evaluation outputs

At minimum: pre-failure trigger coverage, missed-event rate, unnecessary/false mobility-preparation trigger rate, warning time, precision/recall or equivalent event metrics, Brier/calibration metrics, run-level prediction summaries, `T_req` stratification, held-out pass/constellation stratification, and run-level confidence intervals where appropriate.

## 12. Engineering autonomy

Codex may change Python/Bash implementation, host-specific orchestration, dependencies, a dedicated OAI study checkout, telemetry extraction, replay integration, watchdogs, parsers, predictor implementation and defensive validation.

Codex may not silently change campaign size, repetitions, pass-selection rule, whole-pass holdout, feature-family definitions, causal boundary, horizons, primary NTN architecture or failure-retention rules.
