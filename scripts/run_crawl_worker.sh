#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
PYTHONPATH_VALUE="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
DATA_DIR="${JOB_SPY_DATA_DIR:-$ROOT_DIR/data}"

mkdir -p "$DATA_DIR"

export JOB_SPY_DATA_DIR="$DATA_DIR"
export JOB_SPY_CRAWL_EXECUTION_MODE="${JOB_SPY_CRAWL_EXECUTION_MODE:-worker}"
export JOB_SPY_ENABLE_BACKEND_CONSOLE="${JOB_SPY_ENABLE_BACKEND_CONSOLE:-false}"

exec env PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.crawl_worker --base-dir "$ROOT_DIR"
