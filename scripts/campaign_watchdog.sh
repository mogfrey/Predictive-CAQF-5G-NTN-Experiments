#!/usr/bin/env bash
set -euo pipefail

# Linux/tmux-oriented unattended wrapper. Codex should adapt RUN_ONE to the
# validated host-specific runner before final campaign execution.
ROOT="${CAQF_ROOT:-$HOME/Predictive-CAQF-5G-NTN-Experiments}"
PLAN="${1:-$ROOT/results/freeze/campaign_plan.tsv}"
STATUS="${2:-$ROOT/results/campaign_status.tsv}"
LOCK="$ROOT/results/.campaign_watchdog.lock"

mkdir -p "$ROOT/results"
exec 9>"$LOCK"
flock -n 9 || { echo "watchdog already running"; exit 2; }
[[ -f "$PLAN" ]] || { echo "missing plan: $PLAN" >&2; exit 2; }
touch "$STATUS"

run_one() {
  local condition="$1" rep="$2"
  if command -v caqf-run-one >/dev/null 2>&1; then
    caqf-run-one --condition "$condition" --repeat "$rep"
  else
    echo "No validated caqf-run-one command installed; refusing to invent host commands." >&2
    return 64
  fi
}

while IFS=$'\t' read -r condition rep; do
  [[ -z "${condition:-}" || "$condition" == \#* ]] && continue
  if grep -Fqx "$condition"$'\t'"$rep"$'\tDONE' "$STATUS"; then continue; fi
  printf '%s\t%s\tRUNNING\t%s\n' "$condition" "$rep" "$(date -u +%FT%TZ)" >> "$STATUS"
  if run_one "$condition" "$rep"; then
    printf '%s\t%s\tDONE\t%s\n' "$condition" "$rep" "$(date -u +%FT%TZ)" >> "$STATUS"
  else
    rc=$?
    printf '%s\t%s\tFAILED_RC_%s\t%s\n' "$condition" "$rep" "$rc" "$(date -u +%FT%TZ)" >> "$STATUS"
    echo "Campaign paused on $condition repetition $rep (rc=$rc)." >&2
    exit "$rc"
  fi
done < "$PLAN"

echo "Campaign plan exhausted successfully. Run batch QC before declaring completion."
