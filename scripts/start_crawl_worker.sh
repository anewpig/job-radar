#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/app}"

mkdir -p "${JOB_SPY_DATA_DIR:-$APP_DIR/data}"

exec job-radar-crawl-worker --base-dir "$APP_DIR"
