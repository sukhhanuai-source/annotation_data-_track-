#!/usr/bin/env bash
set -euo pipefail

# Poll a local batch folder for new/updated JSONs, then DVC add, commit, dvc push, git push.
#
# Required env:
#   BATCH    : batch folder name under data/raw (e.g., 2026-03-13_raiotransection_LCMS_DME_PKG1_L3)
# Optional env:
#   INTERVAL : seconds between polls (default: 60)
#   PUSH     : 1 to git push after commit (default: 1)
#
# Usage example:
#   BATCH=2026-03-13_raiotransection_LCMS_DME_PKG1_L3 \
#   INTERVAL=60 PUSH=1 \
#   scripts/auto_watch_local_labels.sh

ROOT_DIR="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
cd "$ROOT_DIR"

if [[ -z "${BATCH:-}" ]]; then
  echo "BATCH is required (e.g., BATCH=2026-03-13_raiotransection_LCMS_DME_PKG1_L3)" >&2
  exit 1
fi

INTERVAL="${INTERVAL:-60}"
PUSH="${PUSH:-1}"
WATCH_DIR="data/raw/$BATCH"
STATE_FILE="/tmp/dvc_label_watch_${BATCH//[^a-zA-Z0-9]/_}.md5"
LOCKFILE="/tmp/dvc_label_watch_${BATCH//[^a-zA-Z0-9]/_}.lock"

exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "Another watcher is running for $BATCH (lock $LOCKFILE). Exiting."
  exit 0
fi

mkdir -p "$WATCH_DIR"

snapshot() {
  # Stable, deterministic snapshot of JSON contents (paths + hashes).
  find "$WATCH_DIR" -type f -name "*.json" -print0 \
    | sort -z \
    | xargs -0 md5sum 2>/dev/null
}

while true; do
  CURRENT="$(snapshot || true)"
  if [[ -f "$STATE_FILE" ]]; then
    PREV="$(cat "$STATE_FILE")"
  else
    PREV=""
  end

  if [[ "$CURRENT" != "$PREV" ]]; then
    echo "[watch] $(date -Is) detected JSON changes in $WATCH_DIR"
    echo "$CURRENT" > "$STATE_FILE"

    echo "[watch] DVC add..."
    dvc add "$WATCH_DIR"

    echo "[watch] git add..."
    git add "$WATCH_DIR.dvc"

    echo "[watch] git commit..."
    git commit -m "data: auto sync labels for $BATCH" || echo "[watch] nothing to commit."

    echo "[watch] dvc push..."
    dvc push

    if [[ "$PUSH" == "1" ]]; then
      echo "[watch] git push..."
      git push || echo "[watch] git push failed; check credentials."
    fi
  fi

  sleep "$INTERVAL"
done
