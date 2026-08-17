#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-FINAL_RESULTS}"
[[ -d "$ROOT" ]] || { echo "missing final results directory: $ROOT" >&2; exit 2; }

required=(
  00_HANDOFF
  01_ENVIRONMENT
  02_CODE_SNAPSHOT
  03_CONFIG_FREEZE
  04_ORBITAL_INPUTS
  05_ENGINEERING_VALIDATION
  06_CONTROLLED_RUNS
  07_TLE_PREDICTIVE_RUNS
  08_PROCESSED
  09_QC
)
for d in "${required[@]}"; do
  [[ -d "$ROOT/$d" ]] || { echo "missing required directory: $ROOT/$d" >&2; exit 2; }
done

(
  cd "$ROOT"
  find . -type f ! -name 'SHA256_ALL_FILES.txt' -print0 | sort -z | xargs -0 sha256sum > SHA256_ALL_FILES.txt
  sha256sum -c SHA256_ALL_FILES.txt | tee 09_QC/hash_validation.txt
)

DATE_UTC="$(date -u +%Y%m%d)"
ZIP_NAME="PREDICTIVE_CAQF_5G_NTN_FINAL_RESULTS_${DATE_UTC}.zip"
zip -r -9 "$ZIP_NAME" "$ROOT"
sha256sum "$ZIP_NAME" | tee "${ZIP_NAME}.sha256"
echo "$ZIP_NAME"
