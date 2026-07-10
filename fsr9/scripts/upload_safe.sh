#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-/dev/ttyUSB0}"
PIO="${PIO:-/home/enders/.platformio/penv/bin/pio}"

if command -v fuser >/dev/null 2>&1 && [ -e "$PORT" ]; then
  fuser -k "$PORT" >/dev/null 2>&1 || true
  sleep 1
fi

cd "$PROJECT_DIR"
"$PIO" run --target upload
