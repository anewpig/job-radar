#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
PYTHONPATH_VALUE="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

exec env PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.sqlite_restore_drill --base-dir "$ROOT_DIR" "$@"
