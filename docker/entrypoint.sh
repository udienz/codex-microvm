#!/bin/sh
set -eu

mkdir -p /workspace "${CODEX_HOME:-/home/codex/.codex}"

if [ -z "${API_BEARER_TOKEN:-}" ]; then
  echo "ERROR: API_BEARER_TOKEN must be set" >&2
  exit 1
fi

exec uvicorn app:app --app-dir /app --host 0.0.0.0 --port 8080
