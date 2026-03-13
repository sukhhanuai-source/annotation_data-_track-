#!/usr/bin/env bash
set -euo pipefail

# Sync label JSONs from S3 into a batch folder, track with DVC, commit, and push.
#
# Usage:
#   BUCKET=raiotransection \
#   PREFIX=output/frames/lane_data/LCMS_DME_PKG1_L3/ \
#   BATCH=2026-03-13_raiotransection_LCMS_DME_PKG1_L3 \
#   scripts/auto_sync_s3_labels.sh
#
# Env vars:
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION (required)
#   BUCKET   : S3 bucket name (default: raiotransection)
#   PREFIX   : S3 prefix containing JSONs (default: output/frames/lane_data/LCMS_DME_PKG1_L3/)
#   BATCH    : batch folder under data/raw (default: 2026-03-13_raiotransection_LCMS_DME_PKG1_L3)
#   COMMIT   : 1 to auto-commit (default: 1). Set to 0 to skip git commit.
#   PUSH     : 1 to git push after commit (default: 0).

ROOT_DIR="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
cd "$ROOT_DIR"

BUCKET="${BUCKET:-raiotransection}"
PREFIX="${PREFIX:-output/frames/lane_data/LCMS_DME_PKG1_L3/}"
BATCH="${BATCH:-2026-03-13_raiotransection_LCMS_DME_PKG1_L3}"
COMMIT="${COMMIT:-1}"
PUSH="${PUSH:-0}"

DEST="data/raw/$BATCH"
mkdir -p "$DEST"

echo "Syncing JSONs from s3://$BUCKET/$PREFIX to $DEST ..."
aws s3 sync "s3://$BUCKET/$PREFIX" "$DEST" --exclude "*" --include "*.json"

echo "Tracking with DVC..."
dvc add "$DEST"

echo "Staging git pointers..."
git add "$DEST.dvc"

if [[ "$COMMIT" == "1" ]]; then
  git commit -m "data: sync labels for $BATCH" || echo "No changes to commit."
fi

echo "Pushing data to DVC remote..."
dvc push

if [[ "$PUSH" == "1" ]]; then
  echo "Pushing git changes..."
  git push || echo "git push failed (check credentials/remote)."
fi

echo "Done."
