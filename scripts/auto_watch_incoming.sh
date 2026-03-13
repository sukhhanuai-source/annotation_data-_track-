#!/usr/bin/env bash
set -euo pipefail

# Lightweight watcher: polls incoming/ for new folders and ingests them via DVC.
# Usage:
#   POLL_INTERVAL=30 scripts/auto_watch_incoming.sh
# Notes:
#   - If the folder name already starts with YYYY-MM-DD_, that is used as the batch id.
#   - Otherwise, today's date is prefixed (YYYY-MM-DD_<foldername>).
#   - Marks progress with .ingesting and .done files inside each incoming folder.

ROOT_DIR="$(git -C "$(dirname "$0")/.." rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INCOMING="$ROOT_DIR/incoming"
POLL_INTERVAL="${POLL_INTERVAL:-30}"

# Prevent multiple concurrent watchers
LOCKFILE="/tmp/dvc_watch_incoming.lock"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "Another watcher is running (lock $LOCKFILE). Exiting."
  exit 0
fi

echo "Watching $INCOMING every ${POLL_INTERVAL}s ..."

while true; do
  shopt -s nullglob
  for DIR in "$INCOMING"/*; do
    [[ -d "$DIR" ]] || continue
    BASE="$(basename "$DIR")"
    MARK_ING="$DIR/.ingesting"
    MARK_DONE="$DIR/.done"

    # Skip if already processed or in-progress
    [[ -f "$MARK_DONE" || -f "$MARK_ING" ]] && continue

    # Determine batch id
    if [[ "$BASE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}_ ]]; then
      BATCH="$BASE"
    else
      BATCH="$(date +%F)_$BASE"
    fi

    echo "Found new drop: $DIR -> batch $BATCH"
    touch "$MARK_ING"
    if scripts/auto_ingest_batch.sh "$DIR" "$BATCH"; then
      touch "$MARK_DONE"
      echo "Ingested $BATCH"
    else
      echo "Ingest failed for $DIR (see output)" >&2
    fi
    rm -f "$MARK_ING"
  done
  sleep "$POLL_INTERVAL"
done
