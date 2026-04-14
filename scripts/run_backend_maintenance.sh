#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
PYTHONPATH_VALUE="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
KEEP_LAST="${JOB_SPY_SQLITE_BACKUP_KEEP_LAST:-14}"
INCLUDE_RUNTIME="${JOB_SPY_SQLITE_BACKUP_INCLUDE_RUNTIME:-false}"
FORCE_CLEANUP="${JOB_SPY_BACKEND_MAINTENANCE_FORCE_CLEANUP:-true}"

if [ "$INCLUDE_RUNTIME" = "true" ]; then
  include_runtime_flag="--include-runtime-backup"
else
  include_runtime_flag=""
fi

if [ "$FORCE_CLEANUP" = "true" ]; then
  force_cleanup_flag="--force-cleanup"
else
  force_cleanup_flag=""
fi

exec env PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.backend_maintenance \
  --base-dir "$ROOT_DIR" \
  --trigger scheduled \
  --keep-last-backups "$KEEP_LAST" \
  $include_runtime_flag \
  $force_cleanup_flag
