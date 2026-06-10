import time
from agent_core import setup_logging

logger = setup_logging("agent_processor")

def run():
    logger.info("Starting Processor Agent...")
    # In a real scenario, this would pick up raw IQ data from 'data_capture',
    # perform FFT, and save processed CSV/JSON to 'data_upload'.
    # Currently, 'agent_acquisition' does this directly for simplicity.
    while True:
        time.sleep(60)

if __name__ == "__main__":
    run()
