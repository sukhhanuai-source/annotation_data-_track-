#!/usr/bin/env bash
set -euo pipefail

# Poll S3 for new/updated label JSONs and push via DVC automatically.
#
# Env vars (same as auto_sync_s3_labels.sh):
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION (required)
#   BUCKET   : S3 bucket (default: raiotransection)
#   PREFIX   : S3 prefix with JSONs (default: output/frames/lane_data/LCMS_DME_PKG1_L3/)
#   BATCH    : batch folder under data/raw (default: 2026-03-13_raiotransection_LCMS_DME_PKG1_L3)
#   INTERVAL : seconds between polls (default: 300)
#   COMMIT   : 1 to auto-commit (default: 1)
#   PUSH     : 1 to git push after each sync (default: 0)
#
# Usage:
#   BUCKET=raiotransection PREFIX=output/frames/lane_data/LCMS_DME_PKG1_L3/ \
#   BATCH=2026-03-13_raiotransection_LCMS_DME_PKG1_L3 \
#   INTERVAL=300 \
#   ./scripts/auto_sync_s3_labels_loop.sh
#
# The script uses a lock file to avoid multiple concurrent loops.

ROOT_DIR="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
cd "$ROOT_DIR"

BUCKET="${BUCKET:-raiotransection}"
PREFIX="${PREFIX:-output/frames/lane_data/LCMS_DME_PKG1_L3/}"
BATCH="${BATCH:-2026-03-13_raiotransection_LCMS_DME_PKG1_L3}"
INTERVAL="${INTERVAL:-300}"
COMMIT="${COMMIT:-1}"
PUSH="${PUSH:-0}"

LOCKFILE="/tmp/dvc_sync_labels.lock"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "Another auto_sync_s3_labels_loop is running (lock $LOCKFILE); exiting."
  exit 0
fi

while true; do
  echo "[sync] $(date -Is) syncing labels from s3://$BUCKET/$PREFIX ..."
  BUCKET="$BUCKET" PREFIX="$PREFIX" BATCH="$BATCH" COMMIT="$COMMIT" \
    PUSH="$PUSH" \
    scripts/auto_sync_s3_labels.sh || echo "[sync] run failed (see above)"
  echo "[sync] sleeping ${INTERVAL}s"
  sleep "$INTERVAL"
done
