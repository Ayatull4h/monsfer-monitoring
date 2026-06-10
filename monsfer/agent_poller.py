import time
import requests
import os
from pathlib import Path
from agent_core import load_config, setup_logging

logger = setup_logging("agent_poller")
RUNNING_FLAG = Path("RUNNING_FLAG")

def run():
    logger.info("Starting Command Poller...")
    if not RUNNING_FLAG.exists():
        RUNNING_FLAG.touch()

    while True:
        try:
            config = load_config()
            # Simulate polling
            # resp = requests.get(...)
            
            # Mock commands for demonstration
            # In real scenario, we parse commands to start/stop acquisition
            
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in poller: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
