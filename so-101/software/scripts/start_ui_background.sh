#!/usr/bin/env bash
set -euo pipefail

SOFTWARE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-/dev/ttyUSB0}"
PID_FILE="$SOFTWARE_DIR/.ui-bridge.pid"
LOG_FILE="$SOFTWARE_DIR/.ui-bridge.log"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" >/dev/null 2>&1; then
  echo "FSR UI bridge is already running: http://127.0.0.1:8090"
  exit 0
fi

cd "$SOFTWARE_DIR"
nohup ./scripts/start_ui.sh "$PORT" >"$LOG_FILE" 2>&1 &
echo "$!" >"$PID_FILE"

echo "FSR UI bridge started: http://127.0.0.1:8090"
echo "Log: $LOG_FILE"
