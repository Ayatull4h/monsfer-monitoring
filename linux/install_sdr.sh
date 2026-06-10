#!/bin/bash
set -euo pipefail
# install_sdr.sh — Instalasi Monsfer SDR Agent untuk deployment banyak site
# Usage:
#   ./install_sdr.sh --station 07001 --site "plamongan indah"

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../monsfer" && pwd)"
SERVER_URL="${SERVER_URL:-http://10.100.80.140:5000}"
STATION_ID="${STATION_ID:-07001}"
SITE="${SITE:-plamongan indah}"
OWNER="${OWNER:-semarang}"
TOKEN="${TOKEN:-default}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --station|-i) STATION_ID="$2"; shift 2;;
    --site) SITE="$2"; shift 2;;
    --owner|-o) OWNER="$2"; shift 2;;
    --server|-s) SERVER_URL="$2"; shift 2;;
    --token|-t) TOKEN="$2"; shift 2;;
    *) shift 1;;
  esac
done

echo "=== Installasi Monsfer SDR Agent ==="
echo "Server    : $SERVER_URL"
echo "Station   : $STATION_ID"
echo "Site      : $SITE"
echo "Owner     : $OWNER"
echo ""

# 1. Install system dependencies
echo "[1/5] Install system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv rtl-sdr librtlsdr-dev nmcli 2>/dev/null || true

# 2. Setup virtual environment
echo "[2/5] Setup Python virtual environment..."
cd "$BASE_DIR"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Generate config via bootstrap
echo "[3/5] Generate agent config..."
chmod +x bootstrap_monsfer.sh
./bootstrap_monsfer.sh \
    --server "$SERVER_URL" \
    --station "$STATION_ID" \
    --site "$SITE" \
    --owner "$OWNER" \
    --token "$TOKEN"

# 4. Verify SDR dongle
echo "[4/5] Verifikasi RTL-SDR dongle..."
if command -v rtl_test &>/dev/null; then
    rtl_test -t 2>/dev/null && echo "  Dongle OK" || echo "  WARNING: Dongle tidak terdeteksi. Cek USB."
else
    echo "  SKIP: rtl_test tidak ditemukan"
fi

# 5. Start agents
echo "[5/5] Start all agents..."
chmod +x start_agent.sh
./start_agent.sh start

echo ""
echo "=== Instalasi Selesai ==="
echo "Cek status : ./start_agent.sh status"
echo "Lihat log  : ls -la logs/"
echo "Matikan    : ./start_agent.sh stop"
