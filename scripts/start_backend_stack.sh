#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
STREAMLIT_PORT="${PORT:-8501}"
DATA_DIR="${JOB_SPY_DATA_DIR:-$ROOT_DIR/data}"
PYTHONPATH_VALUE="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p "$DATA_DIR"

export JOB_SPY_DATA_DIR="$DATA_DIR"
export JOB_SPY_CRAWL_EXECUTION_MODE="${JOB_SPY_CRAWL_EXECUTION_MODE:-worker}"
export JOB_SPY_ENABLE_BACKEND_CONSOLE="${JOB_SPY_ENABLE_BACKEND_CONSOLE:-false}"

scheduler_pid=""
worker_pid=""

cleanup() {
  trap - INT TERM EXIT
  for pid in "$scheduler_pid" "$worker_pid"; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      wait "$pid" 2>/dev/null || true
    fi
  done
}

trap cleanup INT TERM EXIT

PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.crawl_scheduler --base-dir "$ROOT_DIR" &
scheduler_pid=$!
PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m job_spy_tw.crawl_worker --base-dir "$ROOT_DIR" &
worker_pid=$!

PYTHONPATH="$PYTHONPATH_VALUE" "$PYTHON_BIN" -m streamlit run "$ROOT_DIR/app.py" \
  --server.address=0.0.0.0 \
  --server.port="$STREAMLIT_PORT" \
  --server.headless=true
app_exit_code=$?

cleanup
exit "$app_exit_code"
