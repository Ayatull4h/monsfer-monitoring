import os
import configparser
from pathlib import Path

def expand_path(path):
    """Expand environment variables and relative paths"""
    # Get the current user's home directory
    home_dir = os.path.expanduser('~')
    
    # Replace ${HOME} with actual home directory
    if '${HOME}' in path:
        path = path.replace('${HOME}', home_dir)
    # Handle legacy ${USER_HOME} for backward compatibility
    elif '${USER_HOME}' in path:
        path = path.replace('${USER_HOME}', home_dir)
    
    # Expand any remaining environment variables
    path = os.path.expandvars(path)
    # Expand user directory if needed
    path = os.path.expanduser(path)
    
    return path

# Read configuration file
config = configparser.ConfigParser()
config_path = Path(__file__).parent / 'config.cfg'

if not config_path.exists():
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

config.read(config_path)

# Get base directory
base_dir = config['PATHS']['BASE_DIR']
if not base_dir or base_dir == '${USER_HOME}/monsfer-server':
    base_dir = str(Path(__file__).parent.parent)

# Expand paths
config['PATHS']['USER_HOME'] = os.path.expanduser('~')
config['PATHS']['BASE_DIR'] = expand_path(base_dir)
config['PATHS']['USERDATA_DIR'] = expand_path(config['PATHS']['USERDATA_DIR'])
config['PATHS']['DB_DIR'] = expand_path(config['PATHS']['DB_DIR'])
config['PATHS']['LOG_DIR'] = expand_path(config['PATHS']['LOG_DIR'])
config['PATHS']['UPLOAD_DIR'] = expand_path(config['PATHS']['UPLOAD_DIR'])
config['PATHS']['SPECTRUM_UPLOAD_DIR'] = expand_path(config['PATHS']['SPECTRUM_UPLOAD_DIR'])
config['PATHS']['DB_FILE'] = expand_path(config['PATHS']['DB_FILE'])
config['PATHS']['APP_LOG'] = expand_path(config['PATHS']['APP_LOG'])
config['PATHS']['SERVER_LOG'] = expand_path(config['PATHS']['SERVER_LOG'])
config['PATHS']['ACTIVITY_LOG'] = expand_path(config['PATHS']['ACTIVITY_LOG'])

# Create necessary directories
for dir_path in [
    config['PATHS']['DB_DIR'],
    config['PATHS']['USERDATA_DIR'],
    config['PATHS']['LOG_DIR'],
    config['PATHS']['UPLOAD_DIR'],
    config['PATHS']['SPECTRUM_UPLOAD_DIR']
]:
    os.makedirs(dir_path, exist_ok=True)

# Ensure database file exists
db_file = Path(config['PATHS']['DB_FILE'])
db_file.parent.mkdir(parents=True, exist_ok=True)

# Expose configuration sections
PATHS = {
    'USER_HOME': config['PATHS']['USER_HOME'],
    'BASE_DIR': config['PATHS']['BASE_DIR'],
    'DB_DIR': config['PATHS']['DB_DIR'],
    'USERDATA_DIR': config['PATHS']['USERDATA_DIR'],
    'LOG_DIR': config['PATHS']['LOG_DIR'],
    'UPLOAD_DIR': config['PATHS']['UPLOAD_DIR'],
    'SPECTRUM_UPLOAD_DIR': config['PATHS']['SPECTRUM_UPLOAD_DIR'],
    'DB_FILE': config['PATHS']['DB_FILE'],
    'APP_LOG': config['PATHS']['APP_LOG'],
    'SERVER_LOG': config['PATHS']['SERVER_LOG'],
    'ACTIVITY_LOG': config['PATHS']['ACTIVITY_LOG']
}

FLASK_CONFIG = {
    'HOST': config['FLASK']['HOST'],
    'PORT': int(config['FLASK']['PORT']),
    'DEBUG': config['FLASK'].getboolean('DEBUG'),
    'SECRET_KEY': config['FLASK']['SECRET_KEY'],
    'MAX_FILE_SIZE': int(config['FLASK']['MAX_FILE_SIZE'])
}

LOG_CONFIG = {
    'level': config['LOGGING']['LEVEL'],
    'format': config['LOGGING']['FORMAT'],
    'log_file': PATHS['APP_LOG']
}

ID_FORMAT = {
    'UPT_ID_LENGTH': int(config['ID_FORMAT']['UPT_ID_LENGTH']),
    'SITE_ID_LENGTH': int(config['ID_FORMAT']['SITE_ID_LENGTH'])
}

ADMIN_CONFIG = {
    'USERNAME': config['ADMIN']['USERNAME'],
    'PASSWORD': config['ADMIN']['PASSWORD'],
    'ID_UPT': config['ADMIN']['ID_UPT'],
    'FULLNAME': config['ADMIN']['FULLNAME']
}

# Load token configuration
TOKEN_SALTS = config.get('TOKEN', 'SALTS').split(',')

# Database configuration
DB_CONFIG = {
    'db_path': PATHS['DB_FILE']
} 