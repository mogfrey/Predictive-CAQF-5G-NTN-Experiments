#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$HOME/Predictive-CAQF-5G-NTN-Experiments}"
cd "$ROOT"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
caqf-exp validate-config --campaign config/campaign.yaml
printf '\nBootstrap complete. Copy config/testbed.example.yaml to config/testbed.local.yaml and fill only confirmed values.\n'
