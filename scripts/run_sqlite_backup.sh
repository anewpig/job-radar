#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
PYTHONPATH_VALUE="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
KEEP_LAST="${JOB_SPY_SQLITE_BACKUP_KEEP_LAST:-14}"
INCLUDE_RUNTIME="${JOB_SPY_SQLITE_BACKUP_INCLUDE_RUNTIME:-false}"

if [ "$INCLUDE_RUNTIME" = "true" ]; then
  exec env PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.sqlite_backup \
    backup \
    --base-dir "$ROOT_DIR" \
    --keep-last "$KEEP_LAST" \
    --include-runtime
else
  exec env PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.sqlite_backup \
    backup \
    --base-dir "$ROOT_DIR" \
    --keep-last "$KEEP_LAST"
fi
