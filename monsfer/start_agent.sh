#!/bin/bash

# Activate venv
source venv/bin/activate

# Start all agents in background
echo "Starting Agents..."

nohup python3 agent_health.py > /dev/null 2>&1 &
echo "Started Health Agent (PID: $!)"

nohup python3 agent_wifi.py > /dev/null 2>&1 &
echo "Started WiFi Agent (PID: $!)"

nohup python3 agent_sync.py > /dev/null 2>&1 &
echo "Started Sync Agent (PID: $!)"

nohup python3 agent_acquisition.py > /dev/null 2>&1 &
echo "Started Acquisition Agent (PID: $!)"

nohup python3 agent_poller.py > /dev/null 2>&1 &
echo "Started Poller Agent (PID: $!)"

nohup python3 agent_ui.py > /dev/null 2>&1 &
echo "Started Local Agent UI (PID: $!) on Port 5100"

echo "All agents started."
