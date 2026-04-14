#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "找不到 $PYTHON_BIN，請先建立虛擬環境。" >&2
  exit 1
fi

export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PYTHON_BIN" -m job_spy_tw.auth_secrets --base-dir "$ROOT_DIR" "$@"
