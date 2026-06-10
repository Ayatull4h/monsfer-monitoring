#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_URL="${SERVER_URL:-http://10.100.80.140:5000}"
OWNER="${OWNER:-semarang}"
SITE="${SITE:-plamongan indah}"
STATION_ID="${STATION_ID:-07plamongan_indah}"
TOKEN="${TOKEN:-default}"
RUN_USER="${RUN_USER:-$(id -un)}"
PY="${PYTHON_BIN:-python3}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --server|-s) SERVER_URL="$2"; shift 2;;
    --owner|-o) OWNER="$2"; shift 2;;
    --site) SITE="$2"; shift 2;;
    --station|-i) STATION_ID="$2"; shift 2;;
    --token|-t) TOKEN="$2"; shift 2;;
    --user|-u) RUN_USER="$2"; shift 2;;
    *) shift 1;;
  esac
done
mkdir -p "${BASE_DIR}/config" "${BASE_DIR}/data_capture" "${BASE_DIR}/data_upload" "${BASE_DIR}/data_archive" "${BASE_DIR}/logs" "${BASE_DIR}/systemd"
cat > "${BASE_DIR}/config/agent_config.json" <<EOF
{
  "station_id": "${STATION_ID}",
  "token": "${TOKEN}",
  "server_url": "${SERVER_URL}",
  "directories": {
    "data": "data_capture",
    "upload": "data_upload",
    "archive": "data_archive",
    "logs": "logs"
  },
  "network": {
    "timeout_sec": 10,
    "retries": 5
  },
  "disk_policy": {
    "max_usage_percent": 85,
    "min_free_gb": 1.0,
    "retention_days": 1,
    "max_archive_size_mb": 500
  },
  "intervals": {
    "health_check": 30,
    "sync": 15,
    "cleanup": 300,
    "acquisition_interval": 30,
    "wifi_interval": 60
  }
}
EOF

cat > "${BASE_DIR}/systemd/sdr-agent-health.service" <<EOF
[Unit]
Description=SDR Health Agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=${BASE_DIR}
ExecStart=/usr/bin/python3 ${BASE_DIR}/agent_health.py
Restart=always
RestartSec=5
User=${RUN_USER}
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
EOF
cat > "${BASE_DIR}/systemd/sdr-agent-wifi.service" <<EOF
[Unit]
Description=SDR WiFi Agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=${BASE_DIR}
ExecStart=/usr/bin/python3 ${BASE_DIR}/agent_wifi.py
Restart=always
RestartSec=5
User=${RUN_USER}
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
EOF
cat > "${BASE_DIR}/systemd/sdr-agent-acquisition.service" <<EOF
[Unit]
Description=SDR Spectrum Acquisition Agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=${BASE_DIR}
ExecStart=/usr/bin/python3 ${BASE_DIR}/agent_acquisition.py
Restart=always
RestartSec=5
User=${RUN_USER}
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
EOF
cat > "${BASE_DIR}/systemd/sdr-agent-sync.service" <<EOF
[Unit]
Description=SDR Upload Sync Agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=${BASE_DIR}
ExecStart=/usr/bin/python3 ${BASE_DIR}/agent_sync.py
Restart=always
RestartSec=5
User=${RUN_USER}
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
EOF
if command -v pip3 >/dev/null 2>&1; then pip3 install -r "${BASE_DIR}/requirements.txt" || true; fi
if command -v sudo >/dev/null 2>&1; then
  if [ -d /etc/systemd/system ]; then
    sudo cp "${BASE_DIR}/systemd/"*.service /etc/systemd/system/
    sudo systemctl daemon-reload || true
    sudo systemctl enable sdr-agent-health sdr-agent-wifi sdr-agent-acquisition sdr-agent-sync || true
    sudo systemctl restart sdr-agent-health sdr-agent-wifi sdr-agent-acquisition sdr-agent-sync || true
  fi
fi
echo "server_url=${SERVER_URL}"
echo "owner=${OWNER}"
echo "site=${SITE}"
echo "station_id=${STATION_ID}"
echo "token=${TOKEN}"
echo "done"
