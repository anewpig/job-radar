#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
RUNTIME_ROOT="${JOB_RADAR_RUNTIME_ROOT:-$HOME/.job-radar-runtime}"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
TEMPLATE_DIR="$ROOT_DIR/ops/launchd"
DATA_DIR="${JOB_SPY_DATA_DIR:-$HOME/.job-radar-data}"
LOG_DIR="$DATA_DIR/logs"

mkdir -p "$LAUNCH_AGENTS_DIR" "$LOG_DIR"

"$ROOT_DIR/scripts/sync_launchd_runtime.sh"

install_agent() {
  label="$1"
  template_name="$2"
  script_name="$3"
  target_plist="$LAUNCH_AGENTS_DIR/$label.plist"
  script_path="$RUNTIME_ROOT/scripts/$script_name"

  sed \
    -e "s|__ROOT_DIR__|$RUNTIME_ROOT|g" \
    -e "s|__SCRIPT_PATH__|$script_path|g" \
    -e "s|__LOG_DIR__|$LOG_DIR|g" \
    "$TEMPLATE_DIR/$template_name" > "$target_plist"

  launchctl bootout "gui/$(id -u)" "$target_plist" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$target_plist"
  launchctl enable "gui/$(id -u)/$label"
  launchctl kickstart -k "gui/$(id -u)/$label"
}

install_agent "com.jobradar.crawl-worker" "com.jobradar.crawl-worker.plist.template" "run_crawl_worker.sh"
install_agent "com.jobradar.crawl-scheduler" "com.jobradar.crawl-scheduler.plist.template" "run_crawl_scheduler.sh"
install_agent "com.jobradar.backend-maintenance" "com.jobradar.backend-maintenance.plist.template" "run_backend_maintenance.sh"

echo "Installed launch agents into $LAUNCH_AGENTS_DIR"
echo "Runtime root: $RUNTIME_ROOT"
echo "Shared data dir: $DATA_DIR"
echo "Logs directory: $LOG_DIR"
