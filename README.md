# Predictive CA-QF 5G NTN Experiments

Public reproducibility workspace for the confirmatory experimental campaign of predictive, uncertainty-aware Continuity-Aware QoS Feasibility (CA-QF) over 5G Release-17 NTN.

The manuscript and historical CA-QF data live elsewhere. This repository is the Codex/RAN-host experiment workspace only.

## Scientific objective

Determine whether a serving 5G NTN link should be continued, prepared for mobility, or declared QoS-infeasible by combining current transport feasibility with a causal estimate of whether QoS will survive a required horizon.

Operationally, for service horizon `T_req`, the framework estimates `P(T_rem >= T_req | X_t)` using only information observable at or before decision time `t` (plus deterministic future orbital geometry only when explicitly permitted by the frozen predictor definition).

## Start here

Codex CLI on the RAN host should read, in order:

1. `docs/SCIENTIFIC_CONTRACT.md`
2. `docs/CODEX_MISSION.md`
3. `docs/CODEX_EXECUTION_HANDOFF.md`
4. `docs/EXPERIMENT_OPERATOR_GUIDE.md`

A fresh Codex session can be started with `docs/CODEX_BOOTSTRAP_PROMPT.txt`.

## Repository safety

Do not commit credentials, IMSI/K/OP/OPc values, private host details, manuscript source, or unsanitized sensitive logs. Local testbed configuration belongs in `config/testbed.local.yaml`, which is ignored by Git.

## Approved campaign

The confirmatory campaign contains 55 publishable runs:

- 25 controlled mechanism-validation runs: 5 conditions x 5 repetitions.
- 30 TLE-driven predictive-validation runs: Starlink and OneWeb, high/medium/low passes, 5 repetitions per pass.

Passes are selected by geometry before network outcomes are inspected. Validation holds out the entire orbital pass, not individual repetitions.

## CLI

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
caqf-exp validate-config --campaign config/campaign.yaml
```

The host-specific OAI integration is adapter-driven. Codex may improve engineering implementation but may not silently change the scientific contract.
