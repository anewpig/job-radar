#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-python}"
PYTHONPATH_VALUE="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.backend_status --base-dir "$ROOT_DIR" "$@"
