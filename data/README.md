# Data layout (DVC-managed)

- `data/raw/<YYYY-MM-DD_batchNN>/` — drop each LabelMe export (images + JSON) as an immutable batch.
- `data/splits/<YYYY-MM-DD_batchNN>.yaml` — matching split manifest for that batch (train/val/test lists).
- `data/derived/` — outputs generated from raw data (e.g., COCO/YOLO conversions), tracked via DVC stages.

## Tracking a new batch
```
BATCH=2026-03-13_batch01
dvc add data/raw/$BATCH data/splits/$BATCH.yaml
git add data/raw/$BATCH.dvc data/splits/$BATCH.yaml.dvc .gitignore
git commit -m "data: add $BATCH"
dvc push   # uploads data to .dvc/storage (configurable)
```

### Automatic ingest (preferred)
```
# Drop annotator export into: incoming/<drop_name>/
scripts/auto_ingest_batch.sh incoming/<drop_name> 2026-03-13_batch01 incoming/splits/<drop_name>.yaml

# To skip git staging/commit (e.g., dirty working tree):
SKIP_GIT=1 scripts/auto_ingest_batch.sh incoming/<drop_name>
```

### Always-on watcher (hands-free)
```
# polls incoming/ every 30s; ingests each new folder automatically
POLL_INTERVAL=30 scripts/auto_watch_incoming.sh
```
Rules:
- If folder name already starts with `YYYY-MM-DD_`, that becomes the batch id; otherwise today’s date is prefixed.
- Progress markers: `.ingesting` (in-flight) and `.done` (completed) inside each incoming folder.

### Sync labels from S3 (JSON) automatically
```
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=ap-south-1 \
BUCKET=raiotransection \
PREFIX=output/frames/lane_data/LCMS_DME_PKG1_L3/ \
BATCH=2026-03-13_raiotransection_LCMS_DME_PKG1_L3 \
scripts/auto_sync_s3_labels.sh
```
- Syncs only `*.json` from the bucket/prefix into `data/raw/$BATCH`, runs `dvc add`, `git add`, optional auto-commit, and `dvc push`.
- Set `COMMIT=0` to skip committing if your working tree is dirty.

### Continuous S3 sync (no manual commands)
```
AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=ap-south-1 \
BUCKET=raiotransection \
PREFIX=output/frames/lane_data/LCMS_DME_PKG1_L3/ \
BATCH=2026-03-13_raiotransection_LCMS_DME_PKG1_L3 \
INTERVAL=300 \
PUSH=1 \  # set to 1 to push Git after each sync
scripts/auto_sync_s3_labels_loop.sh
```
- Polls S3 every `INTERVAL` seconds, pulls new/updated `*.json`, DVC-adds, commits (unless `COMMIT=0`), and pushes.
- Uses `/tmp/dvc_sync_labels.lock` to prevent multiple loops.

### Local LabelMe auto-watch (no S3 input)
Point LabelMe’s export/output directory to `data/raw/<BATCH>/` and run:
```
BATCH=2026-03-13_raiotransection_LCMS_DME_PKG1_L3 \
INTERVAL=60 \
PUSH=1 \
scripts/auto_watch_local_labels.sh
```
- Watches the batch folder for JSON changes, runs `dvc add`, git commit, `dvc push`, and `git push` automatically.
- Uses `/tmp/dvc_label_watch_<batch>.lock` and `/tmp/dvc_label_watch_<batch>.md5` for state.

## Restoring a version
```
git checkout <commit-or-tag>
dvc pull && dvc checkout
```

## Notes
- Never mutate an existing batch; create a new dated batch instead. DVC deduplicates unchanged files automatically.
- If you change the remote location, run `dvc remote modify storage url <new-path>` and commit `.dvc/config`.
