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

## Restoring a version
```
git checkout <commit-or-tag>
dvc pull && dvc checkout
```

## Notes
- Never mutate an existing batch; create a new dated batch instead. DVC deduplicates unchanged files automatically.
- If you change the remote location, run `dvc remote modify storage url <new-path>` and commit `.dvc/config`.
