#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${CAQF_ROOT:-$HOME/Predictive-CAQF-5G-NTN-Experiments}"
OPS_ROOT="${CAQF_OPS_ROOT:-$HOME/codex-caqf}"
REMOTE="${CAQF_RCLONE_REMOTE:-gdrive}"
DEST_ROOT="${CAQF_DRIVE_ROOT:-PREDICTIVE_CAQF_ANALYSIS_HANDOFF}"
STATE="$OPS_ROOT/state"
STAGE="$OPS_ROOT/drive_stage"
mkdir -p "$STATE" "$STAGE"

usage(){ echo "usage: $0 status | phase <A|B|C|D> <source_dir> | final <zip> <sha256_file>" >&2; exit 2; }
write_health(){
  local state="$1" msg="$2" latest="${3:-}"
  python3 - "$STATE/drive_health.json" "$state" "$msg" "$latest" <<'PY'
import json,sys
from datetime import datetime,timezone
p,state,msg,latest=sys.argv[1:]
o={"state":state,"last_upload_utc":datetime.now(timezone.utc).isoformat(),"message":msg,"latest_ready":latest or None}
open(p,'w').write(json.dumps(o,indent=2)+'\n')
PY
}
require_rclone(){ command -v rclone >/dev/null || { write_health DEGRADED "rclone not installed"; exit 3; }; rclone listremotes | grep -Fqx "${REMOTE}:" || { write_health DEGRADED "rclone remote ${REMOTE}: not configured"; exit 4; }; }
safe_copy(){ local src="$1" dst="$2"; rclone copy "$src" "${REMOTE}:${DEST_ROOT}/${dst}" --create-empty-src-dirs; }

require_rclone
case "${1:-}" in
  status)
    tmp="$STAGE/status_$(date -u +%Y%m%dT%H%M%SZ)"; mkdir -p "$tmp"
    for f in campaign_status.json run_index.csv watchdog_health.json dashboard_snapshot.json drive_health.json recent_event.json; do
      for p in "$STATE/$f" "$REPO_ROOT/results/$f" "$REPO_ROOT/results/final/$f"; do [[ -f "$p" ]] && { cp "$p" "$tmp/$f"; break; }; done
    done
    safe_copy "$tmp" "00_status"
    rclone lsf "${REMOTE}:${DEST_ROOT}/00_status" >/dev/null
    write_health OK "incremental status upload/read-back passed"
    rm -rf "$tmp"
    ;;
  phase)
    [[ $# -eq 3 ]] || usage
    phase="${2^^}"; src="$3"; [[ -d "$src" ]] || { echo "missing source dir: $src" >&2; exit 5; }
    case "$phase" in
      A) sub=01_controlled; name=PHASE_A_CONTROLLED_ANALYSIS ;;
      B) sub=02_starlink; name=PHASE_B_STARLINK_ANALYSIS ;;
      C) sub=03_oneweb; name=PHASE_C_ONEWEB_ANALYSIS ;;
      D) sub=04_predictive_analysis; name=PHASE_D_PREDICTIVE_ANALYSIS ;;
      *) usage ;;
    esac
    work="$STAGE/$name"; rm -rf "$work"; mkdir -p "$work/unpacked"
    # Source directory must already be sanitized/allow-listed by the experiment pipeline.
    cp -a "$src"/. "$work/unpacked/"
    (cd "$work/unpacked" && find . -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS)
    (cd "$work" && zip -r -9 "$name.zip" unpacked >/dev/null && sha256sum "$name.zip" > "$name.zip.sha256")
    # Atomic external-analysis order: unpacked -> ZIP -> SHA -> READY last.
    safe_copy "$work/unpacked" "$sub/unpacked"
    safe_copy "$work/$name.zip" "$sub"
    safe_copy "$work/$name.zip.sha256" "$sub"
    marker="$work/PHASE_${phase}_READY.txt"; printf 'READY %s\n' "$(date -u +%FT%TZ)" > "$marker"
    safe_copy "$marker" "$sub"
    rclone lsf "${REMOTE}:${DEST_ROOT}/${sub}" | grep -Fq "PHASE_${phase}_READY.txt"
    write_health OK "$phase phase handoff uploaded and verified" "PHASE_${phase}_READY.txt"
    ;;
  final)
    [[ $# -eq 3 ]] || usage
    zipfile="$2"; shafile="$3"; [[ -f "$zipfile" && -f "$shafile" ]] || { echo "missing final package/checksum" >&2; exit 6; }
    safe_copy "$zipfile" "99_final"
    safe_copy "$shafile" "99_final"
    marker="$STAGE/FINAL_READY.txt"; printf 'READY %s\n' "$(date -u +%FT%TZ)" > "$marker"
    safe_copy "$marker" "99_final"
    rclone lsf "${REMOTE}:${DEST_ROOT}/99_final" | grep -Fq FINAL_READY.txt
    write_health OK "final handoff uploaded and verified" FINAL_READY.txt
    touch "$STATE/FINAL_READY"
    ;;
  *) usage ;;
esac
