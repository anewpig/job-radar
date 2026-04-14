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

copy_tree() {
  source_path="$1"
  target_path="$2"
  if [ ! -e "$source_path" ]; then
    return 0
  fi
  mkdir -p "$target_path"
  rsync -a --delete "$source_path"/ "$target_path"/
}

copy_tree "$ROOT_DIR/.venv" "$RUNTIME_ROOT/.venv"
copy_tree "$ROOT_DIR/src" "$RUNTIME_ROOT/src"
copy_tree "$ROOT_DIR/scripts" "$RUNTIME_ROOT/scripts"
copy_tree "$ROOT_DIR/.streamlit" "$RUNTIME_ROOT/.streamlit"
install -m 0644 "$ROOT_DIR/app.py" "$RUNTIME_ROOT/app.py"
install -m 0644 "$ROOT_DIR/pyproject.toml" "$RUNTIME_ROOT/pyproject.toml"
install -m 0644 "$ROOT_DIR/.env" "$RUNTIME_ROOT/.env"
find "$RUNTIME_ROOT/scripts" -type f -name "*.sh" -exec chmod +x {} \;

mkdir -p "$DATA_DIR/logs" "$DATA_DIR/backups"
if [ -d "$ROOT_DIR/data" ]; then
  rsync -a --ignore-existing "$ROOT_DIR/data/" "$DATA_DIR/"
fi

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
