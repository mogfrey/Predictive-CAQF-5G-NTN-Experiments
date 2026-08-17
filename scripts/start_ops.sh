#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="${CAQF_ROOT:-$HOME/Predictive-CAQF-5G-NTN-Experiments}"
OPS_ROOT="${CAQF_OPS_ROOT:-$HOME/codex-caqf}"
SESSION="${CAQF_OPS_TMUX_SESSION:-caqf-ops}"
export CAQF_ROOT="$REPO_ROOT" CAQF_OPS_ROOT="$OPS_ROOT"
command -v tmux >/dev/null || { echo "tmux is required" >&2; exit 2; }
[[ -x "$OPS_ROOT/watchdog/watchdog.sh" ]] || "$REPO_ROOT/scripts/install_ops.sh"

tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION"
tmux new-session -d -s "$SESSION" -n dashboard "CAQF_ROOT='$REPO_ROOT' CAQF_OPS_ROOT='$OPS_ROOT' python3 '$OPS_ROOT/dashboard/status_server.py' 2>&1 | tee -a '$OPS_ROOT/logs/dashboard.log'"
tmux new-window -t "$SESSION" -n watchdog "CAQF_ROOT='$REPO_ROOT' CAQF_OPS_ROOT='$OPS_ROOT' '$OPS_ROOT/watchdog/watchdog.sh'"
printf 'tmux session: %s\n' "$SESSION"
printf 'dashboard: http://%s:%s/\n' "$(hostname -I | awk '{print $1}')" "${CAQF_DASHBOARD_PORT:-8765}"
