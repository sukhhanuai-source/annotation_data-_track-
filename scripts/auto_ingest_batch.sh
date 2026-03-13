#!/usr/bin/env bash
set -euo pipefail

# Automatic LabelMe batch ingest + DVC tracking
# Usage:
#   scripts/auto_ingest_batch.sh <incoming_dir> [batch_name] [split_manifest]
# Example:
#   scripts/auto_ingest_batch.sh incoming/drop1 2026-03-13_batch01 incoming/splits/trainval.yaml
#
# Behavior:
# - Copies incoming files into data/raw/<batch_name> (fails if target exists).
# - Optionally copies split manifest to data/splits/<batch_name>.yaml.
# - Runs `dvc add` on the new data (and split) and `dvc push`.
# - Optionally stages/commits to git unless SKIP_GIT=1 is set.

ROOT_DIR="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
cd "$ROOT_DIR"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <incoming_dir> [batch_name] [split_manifest]" >&2
  exit 1
fi

INCOMING="$1"
BATCH="${2:-$(date +%F)_batch01}"
SPLIT_SRC="${3:-}"

RAW_DEST="data/raw/$BATCH"
SPLIT_DEST="data/splits/$BATCH.yaml"

if [[ -e "$RAW_DEST" ]]; then
  echo "Destination batch already exists: $RAW_DEST" >&2
  exit 1
fi

echo "Ingesting batch: $BATCH"
mkdir -p "$RAW_DEST"
cp -a "$INCOMING"/. "$RAW_DEST"/

if [[ -n "$SPLIT_SRC" ]]; then
  mkdir -p "$(dirname "$SPLIT_DEST")"
  cp "$SPLIT_SRC" "$SPLIT_DEST"
fi

echo "Running dvc add..."
if [[ -n "$SPLIT_SRC" ]]; then
  dvc add "$RAW_DEST" "$SPLIT_DEST"
else
  dvc add "$RAW_DEST"
fi

if [[ "${SKIP_GIT:-0}" != "1" ]]; then
  echo "Staging git pointers..."
  git add "$RAW_DEST.dvc"
  [[ -n "$SPLIT_SRC" ]] && git add "$SPLIT_DEST.dvc"
  git add .gitignore .dvc/config

  if git diff --cached --quiet; then
    echo "Nothing to commit."
  else
    git commit -m "data: add $BATCH"
  fi
else
  echo "SKIP_GIT=1 set; skipping git add/commit."
fi

echo "Pushing data to DVC remote..."
dvc push

echo "Done. Batch stored at: $RAW_DEST"
