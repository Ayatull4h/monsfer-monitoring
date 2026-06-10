import os
import configparser
import json
import logging
from pathlib import Path

class Config:
    def __init__(self, config_file=None):
        # Get the absolute path to the config directory
        current_dir = Path(__file__).parent.absolute()
        
        # If no config_file is provided, use the default one
        if config_file is None:
            config_file = current_dir / 'config.cfg'
        else:
            config_file = Path(config_file)
            
        # Initialize ConfigParser with interpolation disabled
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(str(config_file))
        
        # Server settings
        self.HOST = self.config.get('Server', 'HOST')
        self.PORT = self.config.getint('Server', 'PORT')
        self.DEBUG = self.config.getboolean('Server', 'DEBUG')
        self.SECRET_KEY = self.config.get('Server', 'SECRET_KEY')
        self.CORS_ENABLED = self.config.getboolean('Server', 'CORS_ENABLED')
        self.ALLOWED_ORIGINS = self.config.get('Server', 'ALLOWED_ORIGINS').split(',')
        
        # Directory paths - convert to absolute paths
        base_dir = current_dir.parent
        self.STATIC_DIR = str(base_dir / self.config.get('Directories', 'STATIC_DIR'))
        self.TEMPLATES_DIR = str(base_dir / self.config.get('Directories', 'TEMPLATES_DIR'))
        def _resolve_path(p):
            p_str = str(p)
            if p_str.startswith('/') or (':' in p_str):
                return p_str
            return str(base_dir / p_str)
        self.DATA_DIR = _resolve_path(self.config.get('Directories', 'DATA_DIR'))
        self.USERDATA_PATH = _resolve_path(self.config.get('Directories', 'USERDATA_PATH'))
        self.SUBSERVICE_FILE = _resolve_path(self.config.get('Directories', 'SUBSERVICE_FILE'))
        
        # API endpoints
        self.SPECTRUM_ENDPOINT = self.config.get('API', 'SPECTRUM_ENDPOINT')
        self.HISTORICAL_DATA_ENDPOINT = self.config.get('API', 'HISTORICAL_DATA_ENDPOINT')
        self.MAX_HISTORICAL_DATA = self.config.getint('API', 'MAX_HISTORICAL_DATA')
        
        # Monitoring settings
        self.UPDATE_INTERVAL = self.config.getint('Monitoring', 'UPDATE_INTERVAL')
        self.DEFAULT_VIEW_MODE = self.config.get('Monitoring', 'DEFAULT_VIEW_MODE')
        self.SHOW_GRID = self.config.getboolean('Monitoring', 'SHOW_GRID')
        self.SHOW_MARKERS = self.config.getboolean('Monitoring', 'SHOW_MARKERS')
        self.AUTO_SCALE = self.config.getboolean('Monitoring', 'AUTO_SCALE')
        
        # Chart settings
        self.DEFAULT_CHART_TYPE = self.config.get('Charts', 'DEFAULT_CHART_TYPE')
        self.CHART_HEIGHT = self.config.getint('Charts', 'CHART_HEIGHT')
        self.CHART_WIDTH = self.config.getint('Charts', 'CHART_WIDTH')
        self.CHART_COLORS = self.config.get('Charts', 'CHART_COLORS').split(',')
        
        # Security settings
        self.PASSWORD_SALT = self.config.get('Security', 'PASSWORD_SALT')
        self.TOKEN_EXPIRY = self.config.getint('Security', 'TOKEN_EXPIRY')
        self.MAX_LOGIN_ATTEMPTS = self.config.getint('Security', 'MAX_LOGIN_ATTEMPTS')
        self.LOGIN_TIMEOUT = self.config.getint('Security', 'LOGIN_TIMEOUT')
        
        # Logging settings
        self.LOGGING_ENABLED = self.config.getboolean('Logging', 'LOGGING_ENABLED')
        self.LOG_LEVEL = getattr(logging, self.config.get('Logging', 'LOG_LEVEL'))
        self.LOG_FORMAT = self.config.get('Logging', 'LOG_FORMAT')
        
        # Load subservices
        self._load_subservices()
        
    def _load_subservices(self):
        try:
            with open(self.SUBSERVICE_FILE, 'r') as f:
                data = json.load(f)
                self.subservices = data.get('subservices', [])
        except Exception as e:
            logging.error(f"Error loading subservices: {str(e)}")
            self.subservices = []

# Create global config instance
config = Config() 
