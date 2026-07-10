#!/usr/bin/env bash
set -euo pipefail

SOFTWARE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$SOFTWARE_DIR/.ui-bridge.pid"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
  kill "$(cat "$PID_FILE")"
  rm -f "$PID_FILE"
  echo "SO-101 UI bridge stopped."
else
  fuser -k 8090/tcp >/dev/null 2>&1 || true
  echo "SO-101 UI bridge was not running."
fi
