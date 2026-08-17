#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${CAQF_ROOT:-$HOME/Predictive-CAQF-5G-NTN-Experiments}"
OPS_ROOT="${CAQF_OPS_ROOT:-$HOME/codex-caqf}"
STATE="$OPS_ROOT/state"
LOGS="$OPS_ROOT/logs"
RECOVERY="$OPS_ROOT/recovery"
INTERVAL="${CAQF_WATCHDOG_INTERVAL_S:-30}"
STALE_S="${CAQF_WATCHDOG_STALE_S:-180}"
MAX_REPAIRS="${CAQF_MAX_REPAIRS_PER_SIGNATURE:-3}"
AUTO_RECOVERY="${CAQF_AUTO_RECOVERY:-0}"
mkdir -p "$STATE" "$LOGS" "$RECOVERY"

health="$STATE/watchdog_health.json"
wdlog="$LOGS/watchdog.log"
exec >>"$wdlog" 2>&1

echo "[$(date -u +%FT%TZ)] watchdog starting"

json_write() {
  local state="$1" sig="${2:-}" attempts="${3:-0}" msg="${4:-}"
  python3 - "$health" "$state" "$sig" "$attempts" "$AUTO_RECOVERY" "$msg" <<'PY'
import json,sys
from datetime import datetime,timezone
p,state,sig,attempts,armed,msg=sys.argv[1:]
obj={"state":state,"last_heartbeat_utc":datetime.now(timezone.utc).isoformat(),"failure_signature":sig or None,"repair_attempts":int(attempts),"auto_recovery_armed":armed=="1","message":msg or None}
try:
    old=json.load(open(p))
    for k in ("last_repair_utc","last_repair_rc"):
        if k in old: obj[k]=old[k]
except Exception: pass
open(p,"w").write(json.dumps(obj,indent=2)+"\n")
PY
}

age_s() {
  local f="$1"
  [[ -e "$f" ]] || { echo 999999; return; }
  echo $(( $(date +%s) - $(stat -c %Y "$f") ))
}

signature() {
  local text="$1"
  printf '%s' "$text" | sha256sum | awk '{print substr($1,1,16)}'
}

attempts_for() {
  local sig="$1" f="$STATE/repair_${sig}.count"
  [[ -f "$f" ]] && cat "$f" || echo 0
}

record_attempt() {
  local sig="$1" n
  n=$(( $(attempts_for "$sig") + 1 ))
  echo "$n" > "$STATE/repair_${sig}.count"
  echo "$n"
}

make_packet() {
  local sig="$1" reason="$2" dir="$RECOVERY/${sig}_$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "$dir"
  printf '%s\n' "$reason" > "$dir/reason.txt"
  cp "$health" "$dir/watchdog_health.json" 2>/dev/null || true
  cp "$STATE/campaign_status.json" "$dir/" 2>/dev/null || true
  cp "$STATE/current_run.json" "$dir/" 2>/dev/null || true
  cp "$STATE/ran_health.json" "$dir/" 2>/dev/null || true
  cp "$STATE/drive_health.json" "$dir/" 2>/dev/null || true
  tail -n 250 "$LOGS"/*.log > "$dir/recent_logs.txt" 2>/dev/null || true
  git -C "$REPO_ROOT" status --short > "$dir/repo_status.txt" 2>/dev/null || true
  git -C "$REPO_ROOT" rev-parse HEAD > "$dir/framework_commit.txt" 2>/dev/null || true
  echo "$dir"
}

invoke_repair() {
  local packet="$1" sig="$2" prompt="$OPS_ROOT/watchdog/recovery_prompt.md" cmdfile="$STATE/codex_recovery_command.txt"
  [[ "$AUTO_RECOVERY" == "1" ]] || return 75
  [[ -s "$cmdfile" ]] || { echo "automatic recovery not armed: missing $cmdfile"; return 76; }
  [[ -s "$prompt" ]] || { echo "missing recovery prompt: $prompt"; return 77; }
  local cmd
  cmd="$(cat "$cmdfile")"
  echo "[$(date -u +%FT%TZ)] invoking bounded Codex repair for $sig using packet $packet"
  # The command file is created by the initial interactive Codex session after it
  # verifies the locally installed CLI syntax. It must accept prompt text on stdin.
  { cat "$prompt"; printf '\n\nRECOVERY_PACKET=%s\nFAILURE_SIGNATURE=%s\n' "$packet" "$sig"; } | bash -lc "$cmd"
}

while true; do
  now="$(date -u +%FT%TZ)"
  final_ready="$STATE/FINAL_READY"
  controller_pid_file="$STATE/controller.pid"
  controller_heartbeat="$STATE/controller_heartbeat"
  fault_file="$STATE/current_fault.json"

  if [[ -f "$final_ready" ]]; then
    json_write COMPLETE "" 0 "Final READY observed"
    sleep "$INTERVAL"; continue
  fi

  state=HEALTHY; reason="healthy"; sig=""; attempts=0
  if [[ -f "$fault_file" ]]; then
    kind="$(python3 - "$fault_file" <<'PY'
import json,sys
try: print(json.load(open(sys.argv[1])).get('kind','NEEDS_CODEX'))
except Exception: print('NEEDS_CODEX')
PY
)"
    case "$kind" in
      EXPECTED_CONDITION_FAILURE) state=EXPECTED_CONDITION_FAILURE; reason="condition-induced failure retained as data" ;;
      INFRASTRUCTURE_FAILURE|INSTRUMENTATION_FAILURE) state="$kind"; reason="$kind" ;;
      *) state=NEEDS_CODEX; reason="$kind" ;;
    esac
  elif [[ -f "$controller_pid_file" ]]; then
    pid="$(cat "$controller_pid_file" 2>/dev/null || true)"
    if [[ -z "$pid" || ! -d "/proc/$pid" ]]; then state=CONTROLLER_DEAD; reason="controller pid absent/dead";
    elif (( $(age_s "$controller_heartbeat") > STALE_S )); then state=STALLED; reason="controller heartbeat stale";
    else state=RUNNING; reason="controller alive"; fi
  fi

  case "$state" in
    INFRASTRUCTURE_FAILURE|INSTRUMENTATION_FAILURE|CONTROLLER_DEAD|STALLED|NEEDS_CODEX)
      sig="$(signature "$state:$reason:$(cat "$fault_file" 2>/dev/null || true)")"
      attempts="$(attempts_for "$sig")"
      if (( attempts >= MAX_REPAIRS )); then
        json_write PAUSED "$sig" "$attempts" "repair limit reached for repeated failure"
      else
        json_write NEEDS_CODEX "$sig" "$attempts" "$reason"
        packet="$(make_packet "$sig" "$reason")"
        if [[ "$AUTO_RECOVERY" == "1" ]]; then
          attempts="$(record_attempt "$sig")"
          json_write RECOVERING "$sig" "$attempts" "Codex repair launched"
          set +e
          invoke_repair "$packet" "$sig"
          rc=$?
          set -e
          python3 - "$health" "$rc" <<'PY'
import json,sys
from datetime import datetime,timezone
p,rc=sys.argv[1:]; o=json.load(open(p)); o['last_repair_utc']=datetime.now(timezone.utc).isoformat(); o['last_repair_rc']=int(rc); open(p,'w').write(json.dumps(o,indent=2)+'\n')
PY
        fi
      fi
      ;;
    *) json_write "$state" "" 0 "$reason" ;;
  esac
  sleep "$INTERVAL"
done
