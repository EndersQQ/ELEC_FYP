#!/usr/bin/env bash
set -euo pipefail

SOFTWARE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-/home/enders/.platformio/penv/bin/python}"
PORT="${1:-/dev/ttyUSB0}"

cd "$SOFTWARE_DIR/web-ui"
exec "$PYTHON" bridge.py --port "$PORT" --http-port 8090
