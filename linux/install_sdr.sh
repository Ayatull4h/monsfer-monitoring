#!/bin/bash
# install_sdr.sh
# Instalasi Monsfer SDR Agent untuk deployment banyak site

echo "Memulai instalasi Monsfer SDR Agent..."
sudo apt update
sudo apt install -y python3-pip python3-venv rtl-sdr librtlsdr-dev

# Setup virtual environment
cd ../monsfer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Berikan permission
chmod +x start_agent.sh

echo "Instalasi selesai. Anda dapat menjalankan ./start_agent.sh"
echo "Atau jalankan python auto_simulate.py untuk simulasi otomatis."
