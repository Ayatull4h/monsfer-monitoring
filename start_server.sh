#!/bin/bash

# Start Monitoring UI
echo "Starting Monitoring UI (Dashboard) on Port 5105..."
cd monsfer-server/MONITORING_UI
nohup python3 app.py > ../logs/monitoring_ui.log 2>&1 &
echo "Dashboard PID: $!"
cd ../..

# Start Main Server (Reverse Proxy)
echo "Starting Main Server on Port 5102..."
cd monsfer-server
nohup python3 server.py > logs/server.log 2>&1 &
echo "Server PID: $!"
cd ..

echo "Systems started. Use 'tail -f monsfer-server/logs/server.log' to monitor."
