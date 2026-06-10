from flask import Flask, request, send_from_directory, jsonify, Response, redirect
from flask_cors import CORS
import os
import logging
from datetime import datetime
import hashlib
import shutil
import configparser
from pathlib import Path
import pandas as pd
from script.file_manager import FileManager

# Reverse proxy dependencies (standard library)
import urllib.request
import urllib.error
import urllib.parse

# Load configuration
config = configparser.ConfigParser()
config_path = Path(__file__).parent / 'server.cfg'
config.read(str(config_path))

# Configure logging
log_folder = Path(config['Paths']['log_folder'])
log_folder.mkdir(parents=True, exist_ok=True)

# Create a custom formatter that uses the format from config
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Replace the format placeholders with the actual values
        format_str = config['Logging']['log_format']
        format_str = format_str.replace('{asctime}', self.formatTime(record))
        format_str = format_str.replace('{levelname}', record.levelname)
        format_str = format_str.replace('{message}', record.getMessage())
        return format_str

# Configure logging with custom formatter
logger = logging.getLogger()
logger.setLevel(getattr(logging, config['Logging']['log_level']))

# Create handlers
file_handler = logging.FileHandler(log_folder / config['Logging']['log_file'])
stream_handler = logging.StreamHandler()

# Set formatter
formatter = CustomFormatter()
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

app = Flask(__name__)

# Configure CORS
if config.getboolean('Security', 'enable_cors'):
    CORS(app, resources={r"/*": {"origins": config['Security']['cors_origins'].split(',')}})

# Configuration
UPLOAD_FOLDER = Path(config['Paths']['upload_folder'])
USERDATA_DIR = Path(config['Paths']['userdata_dir'])
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
USERDATA_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = int(config['FileSettings']['max_file_size'])
ALLOWED_EXTENSIONS = set(config['FileSettings']['allowed_extensions'].split(','))

# Initialize FileManager
file_manager = FileManager(
    userdata_path=Path(__file__).parent / 'db' / 'userdata.json',
    base_userdata_dir=USERDATA_DIR
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_user_site_folders(username, site_name):
    """Create subfolders for user's site directory"""
    try:
        # Create base directory path in USERDATA_DIR
        base_dir = USERDATA_DIR / username / site_name
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subfolders
        subfolders = ['health', 'spectrum', 'wifi_scan']
        for subfolder in subfolders:
            (base_dir / subfolder).mkdir(exist_ok=True)
            
        logging.info(f'Created subfolders for {username}/{site_name} in {USERDATA_DIR}')
        return True
    except Exception as e:
        logging.error(f'Error creating subfolders: {str(e)}')
        return False

@app.route('/')
def index():
    return redirect('/login')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'config': {
            'upload_folder': str(UPLOAD_FOLDER),
            'userdata_dir': str(USERDATA_DIR),
            'max_file_size': MAX_FILE_SIZE,
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        }
    })

@app.route('/single-upload.php', methods=['POST'])
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload with validation and logging"""
    try:
        file_key = 'file' if 'file' in request.files else ('myfile' if 'myfile' in request.files else None)
        if not file_key:
            logging.error('Upload failed: No file part in request')
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files[file_key]
        if file.filename == '':
            logging.error('Upload failed: No selected file')
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            logging.error(f'Upload failed: File type not allowed for {file.filename}')
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Create a temporary file to check size
        temp_path = UPLOAD_FOLDER / f'temp_{file.filename}'
        file.save(str(temp_path))
        
        # Check file size
        file_size = os.path.getsize(temp_path)
        if file_size > MAX_FILE_SIZE:
            os.remove(temp_path)
            return jsonify({'error': 'File too large'}), 413
        
        # Calculate file hash
        file_hash = calculate_file_hash(temp_path)
        
        # Use original filename
        final_filename = file.filename
        final_path = UPLOAD_FOLDER / final_filename
        # print(final_path,final_filename)
        # Move file to final location
        shutil.move(str(temp_path), str(final_path))
        
        # Get file size before organization
        file_size = os.path.getsize(final_path)
        
        # Organize the file using FileManager
        if file_manager.organize_file(final_path):
            # If organization is successful, prepare success response
            response = {
                'message': 'File uploaded and organized successfully',
                'filename': final_filename,
                'hash': file_hash,
                'size': file_size
            }
            logging.info(f'File uploaded and organized successfully: {final_filename}')
            return jsonify(response), 200
        else:
            # If organization fails, prepare error response
            response = {
                'error': 'File uploaded but organization failed',
                'filename': final_filename,
                'hash': file_hash,
                'size': file_size
            }
            logging.error(f'File uploaded but organization failed: {final_filename}')
            return jsonify(response), 500
            
    except Exception as e:
        logging.error(f'Upload error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Handle file download with validation"""
    try:
        file_path = UPLOAD_FOLDER / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_from_directory(
            str(UPLOAD_FOLDER),
            filename,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logging.error(f'Download error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/list', methods=['GET'])
def list_files():
    """List all uploaded files"""
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = UPLOAD_FOLDER / filename
            if file_path.is_file():
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
        return jsonify({'files': files}), 200
    except Exception as e:
        logging.error(f'List files error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/read-csv/<path:filename>', methods=['GET'])
def read_csv(filename):
    """Read a CSV file and return its contents as JSON"""
    try:
        file_path = USERDATA_DIR / filename
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
            
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Convert to JSON
        data = df.to_dict(orient='records')
        
        return jsonify({
            'data': data,
            'columns': list(df.columns),
            'filename': filename
        }), 200
    except Exception as e:
        logging.error(f'CSV read error: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Base URLs for internal services to be proxied via port 5102
MONITORING_UI_BASE = "http://127.0.0.1:5105"
SCRIPT_APP_BASE = "http://127.0.0.1:5100"

# Helper to forward requests
def proxy_request(target_base: str, path: str):
    # Build target URL
    query_string = request.query_string.decode('utf-8') if request.query_string else ''
    url = f"{target_base}{path}"
    if query_string:
        url = f"{url}?{query_string}"

    # Map headers (exclude host-related ones)
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-length']}

    # Prepare body for methods
    data = None
    if request.method in ['POST', 'PUT', 'PATCH']:
        data = request.get_data()

    # Perform request
    req = urllib.request.Request(url, data=data, headers=headers, method=request.method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read()
            status = resp.getcode()
            # Collect response headers
            resp_headers = [(k, v) for k, v in resp.getheaders() if k.lower() not in ['content-length', 'transfer-encoding', 'connection']]
            return Response(resp_body, status=status, headers=resp_headers)
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, 'read') else str(e).encode()
        return Response(body, status=e.code)
    except urllib.error.URLError as e:
        return jsonify({'error': 'Upstream unavailable', 'detail': str(e)}), 502

# Reverse proxy routes
@app.route('/monitoring', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@app.route('/monitoring/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def proxy_monitoring(path):
    return proxy_request(MONITORING_UI_BASE, f"/monitoring/{path}" if path else "/monitoring")

@app.route('/portal', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@app.route('/portal/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def proxy_portal(path):
    return proxy_request(SCRIPT_APP_BASE, f"/{path}" if path else "/")

# Proxy root-level static assets for Monitoring UI (because static_url_path='')
@app.route('/js/<path:path>', methods=['GET'])
def proxy_monitoring_js(path):
    return proxy_request(MONITORING_UI_BASE, f"/js/{path}")

@app.route('/css/<path:path>', methods=['GET'])
def proxy_monitoring_css(path):
    return proxy_request(MONITORING_UI_BASE, f"/css/{path}")

@app.route('/fonts/<path:path>', methods=['GET'])
def proxy_monitoring_fonts(path):
    return proxy_request(MONITORING_UI_BASE, f"/fonts/{path}")

# Proxy common pages for Monitoring UI
@app.route('/login', methods=['GET', 'POST'])
def proxy_login():
    return proxy_request(MONITORING_UI_BASE, "/login")

@app.route('/dashboard', methods=['GET'])
def proxy_dashboard():
    return proxy_request(MONITORING_UI_BASE, "/dashboard")

@app.route('/logout', methods=['GET'])
def proxy_logout():
    return proxy_request(MONITORING_UI_BASE, "/logout")

@app.route('/wifi', methods=['GET'])
def proxy_wifi():
    return proxy_request(MONITORING_UI_BASE, "/wifi")

@app.route('/system_info', methods=['GET'])
def proxy_system_info():
    return proxy_request(MONITORING_UI_BASE, "/system_info")

@app.route('/settings', methods=['GET'])
def proxy_settings():
    return proxy_request(MONITORING_UI_BASE, "/settings")

# Proxy API endpoints for Monitoring UI
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def proxy_monitoring_api(path):
    return proxy_request(MONITORING_UI_BASE, f"/api/{path}")

# Proxy favicon (if requested at root)
@app.route('/favicon.ico', methods=['GET'])
def proxy_favicon():
    # Try Monitoring UI favicon first
    return proxy_request(MONITORING_UI_BASE, "/favicon.ico")

if __name__ == '__main__':
    logging.info('Starting server...')
    logging.info(f'Configuration loaded:')
    logging.info(f'- Upload folder: {UPLOAD_FOLDER}')
    logging.info(f'- Userdata directory: {USERDATA_DIR}')
    logging.info(f'- Max file size: {MAX_FILE_SIZE} bytes')
    logging.info(f'- Allowed extensions: {ALLOWED_EXTENSIONS}')
    
    app.run(
        host=config['Server']['host'],
        port=int(config['Server']['port']),
        debug=config.getboolean('Server', 'debug')
    )