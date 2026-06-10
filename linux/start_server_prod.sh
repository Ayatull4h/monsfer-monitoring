#!/bin/bash
# start_server_prod.sh
# Script untuk menjalankan Monsfer Server menggunakan Gunicorn + Gevent di Linux
# Mampu menangani hingga 1000 concurrent users

cd ../monsfer-server
source venv/bin/activate

# Install gunicorn dan gevent jika belum ada
pip install gunicorn gevent

# Jalankan server dengan gunicorn
# -w 4: 4 worker processes
# -k gevent: asynchronous worker class
# --worker-connections 1000: max simultaneous connections per worker
echo "Starting Monsfer Server with Gunicorn (gevent)..."
gunicorn -w 4 -k gevent --worker-connections 1000 --bind 0.0.0.0:5102 server:app
