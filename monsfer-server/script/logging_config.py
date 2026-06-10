import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

class LoggingConfig:
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = Path(log_dir)
        self.max_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure system logger
        self.system_logger = self._setup_logger(
            'system',
            self.log_dir / 'system.log',
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Configure activity logger
        self.activity_logger = self._setup_logger(
            'activity',
            self.log_dir / 'activity.log',
            '%(asctime)s - %(message)s'
        )
        
    def _setup_logger(self, name: str, log_file: Path, format_str: str) -> logging.Logger:
        """Setup individual logger"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_size,
            backupCount=self.backup_count
        )
        
        formatter = logging.Formatter(format_str)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.propagate = False
        
        return logger
        
    def log_activity(self, action: str, details: str, username: str = None):
        """Log user activity with timestamp"""
        user = username or 'Unknown'
        self.activity_logger.info(f"User: {user} | Action: {action} | {details}")
        
    def log_error(self, message: str, exc_info: bool = True):
        """Log error message with optional exception info"""
        self.system_logger.error(message, exc_info=exc_info)
        
    def log_debug(self, message: str):
        """Log debug message"""
        self.system_logger.debug(message) 