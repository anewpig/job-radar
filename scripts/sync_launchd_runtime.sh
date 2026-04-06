#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
RUNTIME_ROOT="${JOB_RADAR_RUNTIME_ROOT:-$HOME/.job-radar-runtime}"
DATA_DIR="${JOB_SPY_DATA_DIR:-$HOME/.job-radar-data}"

mkdir -p "$RUNTIME_ROOT" "$DATA_DIR"

if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "Missing $ROOT_DIR/.env" >&2
  exit 1
fi

clone_copy() {
  source_path="$1"
  target_path="$2"
  rm -rf "$target_path"
  if ! cp -cR "$source_path" "$target_path" 2>/dev/null; then
    cp -R "$source_path" "$target_path"
  fi
}

clone_copy "$ROOT_DIR/.venv" "$RUNTIME_ROOT/.venv"
clone_copy "$ROOT_DIR/src" "$RUNTIME_ROOT/src"
clone_copy "$ROOT_DIR/scripts" "$RUNTIME_ROOT/scripts"
clone_copy "$ROOT_DIR/.streamlit" "$RUNTIME_ROOT/.streamlit"
rm -f "$RUNTIME_ROOT/app.py" "$RUNTIME_ROOT/pyproject.toml" "$RUNTIME_ROOT/.env"
cp -c "$ROOT_DIR/app.py" "$RUNTIME_ROOT/app.py" 2>/dev/null || cp "$ROOT_DIR/app.py" "$RUNTIME_ROOT/app.py"
cp -c "$ROOT_DIR/pyproject.toml" "$RUNTIME_ROOT/pyproject.toml" 2>/dev/null || cp "$ROOT_DIR/pyproject.toml" "$RUNTIME_ROOT/pyproject.toml"
cp -c "$ROOT_DIR/.env" "$RUNTIME_ROOT/.env" 2>/dev/null || cp "$ROOT_DIR/.env" "$RUNTIME_ROOT/.env"

rsync -a "$ROOT_DIR/data/" "$DATA_DIR/"

runtime_env="$RUNTIME_ROOT/.env"
tmp_env="$RUNTIME_ROOT/.env.tmp"
awk -v data_dir="$DATA_DIR" '
  BEGIN { replaced = 0 }
  /^JOB_SPY_DATA_DIR=/ {
    print "JOB_SPY_DATA_DIR=" data_dir
    replaced = 1
    next
  }
  { print }
  END {
    if (replaced == 0) {
      print "JOB_SPY_DATA_DIR=" data_dir
    }
  }
' "$runtime_env" > "$tmp_env"
mv "$tmp_env" "$runtime_env"

echo "Synced launchd runtime to $RUNTIME_ROOT"
echo "Shared data dir: $DATA_DIR"
