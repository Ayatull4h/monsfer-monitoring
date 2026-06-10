#!/bin/bash

echo "--- Universal Agent Installer ---"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 could not be found. Please install it."
    exit 1
fi

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install deps
source venv/bin/activate
echo "Installing dependencies..."
pip install -r requirements.txt

# Configuration
echo ""
echo "--- Configuration ---"
if [ -f "config/agent_config.json" ]; then
    echo "Configuration file already exists."
else
    echo "Creating default configuration..."
    mkdir -p config
    # We rely on the pre-created config or user manual edit for now
    # to keep this script non-interactive for the tool execution
    echo "Please edit config/agent_config.json manually if needed."
fi

# Permissions
chmod +x start_agent.sh

echo ""
echo "Installation Complete!"
echo "Run ./start_agent.sh to start the agent."
