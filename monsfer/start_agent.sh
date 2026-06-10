#!/bin/bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${BASE_DIR}/venv"
PID_DIR="${BASE_DIR}"

AGENTS=(
    "agent_acquisition.py:acquisition"
    "agent_health.py:health"
    "agent_wifi.py:wifi"
    "agent_sync.py:sync"
)

start_all() {
    echo "Starting all SDR agents..."
    for entry in "${AGENTS[@]}"; do
        script="${entry%%:*}"
        name="${entry##*:}"
        pid_file="${PID_DIR}/${name}.pid"

        if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
            echo "  [SKIP] $name already running (PID: $(cat "$pid_file"))"
            continue
        fi

        nohup python3 "${BASE_DIR}/${script}" > /dev/null 2>&1 &
        echo $! > "$pid_file"
        echo "  [START] $name (PID: $!)"
    done
    echo "Done."
}

stop_all() {
    echo "Stopping all SDR agents..."
    for entry in "${AGENTS[@]}"; do
        name="${entry##*:}"
        pid_file="${PID_DIR}/${name}.pid"

        if [ ! -f "$pid_file" ]; then
            echo "  [SKIP] $name (no pid file)"
            continue
        fi

        pid=$(cat "$pid_file")
        if kill "$pid" 2>/dev/null; then
            echo "  [STOP] $name (PID: $pid)"
        else
            echo "  [STOP] $name (not running)"
        fi
        rm -f "$pid_file"
    done
    echo "Done."
}

status_all() {
    echo "SDR Agent Status:"
    echo "-----------------"
    for entry in "${AGENTS[@]}"; do
        name="${entry##*:}"
        pid_file="${PID_DIR}/${name}.pid"

        if [ -f "$pid_file" ] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
            echo "  [RUNNING] $name (PID: $(cat "$pid_file"))"
        else
            echo "  [STOPPED] $name"
        fi
    done
}

case "${1:-start}" in
    start)   start_all ;;
    stop)    stop_all  ;;
    restart) stop_all; sleep 1; start_all ;;
    status)  status_all ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
