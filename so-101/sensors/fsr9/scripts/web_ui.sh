#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-${2:-/dev/ttyUSB0}}"
HTTP_PORT="${HTTP_PORT:-8090}"
PYTHON="${PYTHON:-/home/enders/.platformio/penv/bin/python}"
PID_FILE="$PROJECT_DIR/.ui-bridge.pid"
LOG_FILE="$PROJECT_DIR/.ui-bridge.log"
URL="http://127.0.0.1:$HTTP_PORT"

is_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

start() {
  cd "$PROJECT_DIR"

  if is_running; then
    echo "FSR web UI bridge is already running:"
    echo "  pid: $(cat "$PID_FILE")"
    echo "  url: $URL"
    return
  fi

  : > "$LOG_FILE"
  nohup "$PYTHON" -u web-ui/bridge.py --port "$PORT" --http-port "$HTTP_PORT" >> "$LOG_FILE" 2>&1 &
  echo "$!" > "$PID_FILE"
  sleep 1

  if is_running; then
    echo "FSR web UI bridge started:"
    echo "  pid: $(cat "$PID_FILE")"
    echo "  url: $URL"
    echo "  serial: $PORT"
  else
    echo "FSR web UI bridge failed to start. Log:"
    cat "$LOG_FILE"
    exit 1
  fi
}

stop() {
  if is_running; then
    kill "$(cat "$PID_FILE")"
    rm -f "$PID_FILE"
    echo "FSR web UI bridge stopped."
  else
    rm -f "$PID_FILE"
    echo "FSR web UI bridge is not running."
  fi
}

status() {
  if is_running; then
    echo "FSR web UI bridge is running:"
    echo "  pid: $(cat "$PID_FILE")"
    echo "  url: $URL"
  else
    echo "FSR web UI bridge is not running."
    [ -s "$LOG_FILE" ] && tail -20 "$LOG_FILE"
    exit 1
  fi
}

case "${1:-start}" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    start
    ;;
  status)
    status
    ;;
  log)
    if is_running; then
      echo "FSR web UI bridge is running:"
      echo "  pid: $(cat "$PID_FILE")"
      echo "  url: $URL"
    else
      echo "FSR web UI bridge is not running."
    fi

    if [ -s "$LOG_FILE" ]; then
      echo
      tail -80 "$LOG_FILE"
    else
      echo "No bridge log output yet."
      echo "Start it with: $0 start /dev/ttyUSB0"
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|log} [serial-port]"
    echo "Example: $0 start /dev/ttyUSB0"
    exit 2
    ;;
esac
