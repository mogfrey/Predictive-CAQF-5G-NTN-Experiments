#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="${CAQF_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
OPS_ROOT="${CAQF_OPS_ROOT:-$HOME/codex-caqf}"
mkdir -p "$OPS_ROOT"/{dashboard,watchdog,state,logs,recovery,drive_stage}
cp "$REPO_ROOT/ops/dashboard/index.html" "$OPS_ROOT/dashboard/index.html"
cp "$REPO_ROOT/ops/dashboard/status_server.py" "$OPS_ROOT/dashboard/status_server.py"
cp "$REPO_ROOT/ops/watchdog/watchdog.sh" "$OPS_ROOT/watchdog/watchdog.sh"
cp "$REPO_ROOT/ops/watchdog/recovery_prompt.md" "$OPS_ROOT/watchdog/recovery_prompt.md"
chmod +x "$OPS_ROOT/dashboard/status_server.py" "$OPS_ROOT/watchdog/watchdog.sh"
cat > "$OPS_ROOT/README.txt" <<EOF
Runtime operations workspace for Predictive CA-QF.
Source repository: $REPO_ROOT
Dashboard default port: 8765
Runtime state is intentionally outside Git.
EOF

echo "Installed operations templates to $OPS_ROOT"
echo "Codex must adapt/validate runtime health sources before publishable runs."
