#!/bin/sh
set -eu

mkdir -p "${JOB_SPY_DATA_DIR:-/app/data}"

exec streamlit run /app/app.py \
  --server.address=0.0.0.0 \
  --server.port="${PORT:-8501}" \
  --server.headless=true
