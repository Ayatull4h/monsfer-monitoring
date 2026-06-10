import json
import os
import logging
from pathlib import Path

# Setup Base Paths
BASE_DIR = Path(__file__).parent.absolute()
CONFIG_PATH = BASE_DIR / "config" / "agent_config.json"

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"CRITICAL: Cannot load config: {e}")
        return {}

def setup_logging(name):
    config = load_config()
    log_dir = BASE_DIR / config.get('directories', {}).get('logs', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        filename=os.path.join(log_dir, f'{name}.log'),
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)

def get_paths(config):
    dirs = config.get('directories', {})
    return {
        "data": BASE_DIR / dirs.get('data', 'data_capture'),
        "upload": BASE_DIR / dirs.get('upload', 'data_upload'),
        "archive": BASE_DIR / dirs.get('archive', 'data_archive'),
        "logs": BASE_DIR / dirs.get('logs', 'logs')
    }
