import json
import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
CONFIG_PATH = BASE_DIR / "config" / "agent_config.json"

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"CRITICAL: Cannot load config: {e}")
        return {}

def setup_logging(name):
    config = load_config()
    log_dir = BASE_DIR / config.get('directories', {}).get('logs', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_path = os.path.join(log_dir, f'{name}.log')
    handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=2)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)

    return logger

def get_paths(config):
    dirs = config.get('directories', {})
    return {
        "data": BASE_DIR / dirs.get('data', 'data_capture'),
        "upload": BASE_DIR / dirs.get('upload', 'data_upload'),
        "archive": BASE_DIR / dirs.get('archive', 'data_archive'),
        "logs": BASE_DIR / dirs.get('logs', 'logs')
    }
