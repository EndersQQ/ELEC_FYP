#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-/dev/ttyUSB0}"
HTTP_PORT="${HTTP_PORT:-8090}"
PYTHON="${PYTHON:-/home/enders/.platformio/penv/bin/python}"

cd "$PROJECT_DIR"
exec "$PYTHON" web-ui/bridge.py --port "$PORT" --http-port "$HTTP_PORT"
