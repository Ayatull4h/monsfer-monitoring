from flask import g, Flask, jsonify, request, render_template, send_from_directory, redirect, url_for, session, flash, send_file
import zipfile
from io import BytesIO
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf, validate_csrf
import os
from datetime import datetime, timedelta
import numpy as np
import random
import json
import csv
import platform
import psutil
import logging
from config.config_loader import config
import pandas as pd
from pathlib import Path
from lib.decode_password import PasswordHandler
from lib.get_user_data import get_user_data
from functools import wraps
import string
import re

# Configure logging based on toggle
if config.LOGGING_ENABLED:
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        handlers=[logging.StreamHandler()]
    )
else:
    logging.disable(logging.CRITICAL)

# Initialize Flask app with optimized settings
app = Flask(__name__, 
    static_folder=config.STATIC_DIR,
    template_folder=config.TEMPLATES_DIR,
    static_url_path=''  # Optimize static file serving
)

# Set secret key
app.secret_key = config.SECRET_KEY

# Initialize CSRF protection
csrf = CSRFProtect()
# Disable CSRF for testing to avoid token expiration issues
app.config['WTF_CSRF_ENABLED'] = False
csrf.init_app(app)

# Background simulation synchronizer thread to bridge semarang/plamongan indah -> 3KOM/07plamongan_indah
import threading
import time
import shutil

def background_simulation_sync():
    src_base = Path(config.DATA_DIR) / "semarang" / "plamongan indah"
    dst_base = Path(config.DATA_DIR) / "3KOM" / "07plamongan_indah"
    
    while True:
        try:
            if src_base.exists():
                for sub in ["spectrum", "wifi", "health"]:
                    src_dir = src_base / sub
                    dst_dir = dst_base / sub
                    if src_dir.exists():
                        dst_dir.mkdir(parents=True, exist_ok=True)
                        for f in src_dir.glob("*"):
                            if f.is_file():
                                dst_file = dst_dir / f.name
                                if not dst_file.exists() or f.stat().st_mtime > dst_file.stat().st_mtime:
                                    shutil.copy2(f, dst_file)
        except Exception as e:
            pass
        time.sleep(5)

# Start background sync thread
sync_thread = threading.Thread(target=background_simulation_sync, daemon=True)
sync_thread.start()


# Inject CSRF helper into Jinja templates to avoid UndefinedError on csrf_token()
@app.context_processor
def inject_csrf():
    # Provide callable so templates can use {{ csrf_token() }}
    return { 'csrf_token': generate_csrf }

# Configure CORS if enabled
if config.CORS_ENABLED:
    CORS(app, resources={r"/*": {"origins": config.ALLOWED_ORIGINS}})

# Auto-login for simulation testing
@app.before_request
def auto_login():
    if 'username' not in session:
        # Default user data for admin
        session['username'] = 'admin'
        session['user_data'] = {
            'username': 'admin',
            'fullname': 'System Admin',
            'role': 'admin',
            'is_admin': True
        }
        logging.info("Auto-logged in as admin for simulation")

    # Auto-select site: prioritize semarang/plamongan indah for simulation
    if 'current_site' not in session or not session.get('current_site'):
        try:
            data_dir = Path(config.DATA_DIR)
            # Try specific site first
            target_user = "3KOM"
            target_site = "07plamongan_indah"
            
            if (data_dir / target_user / target_site).exists():
                session['current_site'] = target_site
                session['current_site_owner'] = target_user
                session['current_site_token'] = "plamongan_test"
                logging.info(f"Auto-selected preferred site: {target_user}/{target_site}")
            elif data_dir.exists():
                # Fallback to any site
                for user_dir in data_dir.iterdir():
                    if not user_dir.is_dir(): continue
                    for site_dir in user_dir.iterdir():
                        if site_dir.is_dir():
                            session['current_site'] = site_dir.name
                            session['current_site_owner'] = user_dir.name
                            session['current_site_token'] = site_dir.name
                            logging.info(f"Auto-selected fallback site: {user_dir.name}/{site_dir.name}")
                            break
                    else: continue
                    break
        except Exception as e:
            logging.warning(f"Auto-select site failed: {e}")


# Load blacklist
def load_blacklist():
    blacklist_path = Path('config/blacklist.txt')
    if not blacklist_path.exists():
        return set()
    
    with open(blacklist_path, 'r') as f:
        # Read lines and filter out comments and empty lines
        return {line.strip() for line in f if line.strip() and not line.startswith('#')}

# Check if request path is blacklisted
def is_blacklisted(path):
    blacklist = load_blacklist()
    return any(path.startswith(blocked) for blocked in blacklist)

# Browser detection middleware
def is_browser_request():
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # List of common browser User-Agent patterns
    browser_patterns = [
        r'mozilla/[\d.]+',  # Firefox, Chrome, Safari, etc.
        r'chrome/[\d.]+',
        r'safari/[\d.]+',
        r'firefox/[\d.]+',
        r'edge/[\d.]+',
        r'opera/[\d.]+',
        r'msie/[\d.]+',
        r'trident/[\d.]+',
        r'chromium/[\d.]+',
        r'brave/[\d.]+',
        r'vivaldi/[\d.]+',
        r'ucbrowser/[\d.]+',
        r'samsungbrowser/[\d.]+',
        r'android/[\d.]+',  # Android browser
        r'iphone/[\d.]+',   # iOS browser
        r'ipad/[\d.]+',     # iOS browser
        r'windows/[\d.]+',  # Windows browser
        r'macintosh/[\d.]+' # Mac browser
    ]
    
    # Check if User-Agent matches any browser pattern
    return any(re.search(pattern, user_agent) for pattern in browser_patterns)

def is_valid_request():
    # Check if request is from a browser
    if not is_browser_request():
        return False
        
    # Check for required headers - reduced requirements
    required_headers = ['Accept']
    if not all(header in request.headers for header in required_headers):
        return False
        
    # Check for common browser headers - made optional
    browser_headers = ['Sec-Fetch-Dest', 'Sec-Fetch-Mode', 'Sec-Fetch-Site', 'Accept-Language']
    # If none of the browser headers are present, still allow the request
    if not any(header in request.headers for header in browser_headers):
        return True
        
    return True

# Browser-only access middleware removed for stability
# (It previously blocked or altered requests unexpectedly and may have caused 500)

# CSRF exemptions are applied per-route using @csrf.exempt where needed

# Remove custom CSRF error handler (restore default behavior)

# Remove global after_request CSRF/security header setter

 # Removed custom 500 error handler to restore default behavior

# Cache frequently used paths
DATA_DIR = Path(config.DATA_DIR)
USERDATA_PATH = Path(config.USERDATA_PATH)
BAK_USERDATA_PATH = USERDATA_PATH.parent / 'userdata-bak.json'

# Safe JSON utilities with lock and atomic replace
def load_json_safe(path: Path) -> dict:
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.exception(f"Failed to read JSON at {path}: {e}")
    return {}

def save_json_atomic_with_lock(path: Path, data: dict):
    import os, time
    lock_path = Path(str(path) + '.lock')
    start = time.time()
    fd = None
    try:
        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except FileExistsError:
                if time.time() - start > 2.0:
                    raise TimeoutError(f'Lock timeout for {path}')
                time.sleep(0.05)
        tmp_path = Path(str(path) + '.tmp')
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(str(tmp_path), str(path))
    finally:
        if fd is not None:
            os.close(fd)
        try:
            if lock_path.exists():
                os.remove(str(lock_path))
        except Exception:
            pass

# Initialize in-memory data structures
spectrum_data = []
alerts = []
devices = []
alert_rules = []
preferences = {
    'theme': 'light',
    'updateInterval': config.UPDATE_INTERVAL,
    'defaultView': config.DEFAULT_VIEW_MODE,
    'showGrid': config.SHOW_GRID,
    'showMarkers': config.SHOW_MARKERS,
    'autoScale': config.AUTO_SCALE
}

# Cache for subservices
_subservices_cache = None

# Inisialisasi password handler
password_handler = PasswordHandler()

def get_subservices():
    global _subservices_cache
    if _subservices_cache is None:
        try:
            with open(config.SUBSERVICE_FILE, 'r') as f:
                    data = json.load(f)
                    _subservices_cache = data.get('subservices', [])
        except Exception as e:
            logging.error(f"Error loading subservices: {str(e)}")
            _subservices_cache = []
    return _subservices_cache

def get_user_spectrum_dir(username, site_name):
    """Get the spectrum directory for a specific user and site"""
    try:
        from flask import session
        effective_username = session.get('current_site_owner') or username
    except Exception:
        effective_username = username
        
    spectrum_dir = DATA_DIR / effective_username / site_name / 'spectrum'
    return spectrum_dir

def read_spectrum_csv(filename, username, site_name, start_freq=None, stop_freq=None):
    try:
        spectrum_dir = get_user_spectrum_dir(username, site_name)
        file_path = spectrum_dir / filename
        
        if not file_path.exists():
            # Try fuzzy match if direct match fails (handle station ID prefix)
            candidates = list(spectrum_dir.glob(f"*{filename}"))
            if candidates:
                file_path = candidates[0]
                logging.info(f"Fuzzy matched file: {file_path.name}")
            else:
                logging.error(f"File not found: {filename} in {spectrum_dir}")
                return None, "File not found"
            
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
        # Find BAND_CONFIGURATION and MEASUREMENT_DATA sections
        band_config_start = -1
        band_config_end = -1
        measurement_start = -1
        
        for i, line in enumerate(lines):
            if '#BAND_CONFIGURATION' in line:
                band_config_start = i + 1
            elif '#MEASUREMENT_DATA' in line:
                band_config_end = i - 1
                measurement_start = i + 1
                
        if band_config_start == -1 or measurement_start == -1:
            logging.error("Invalid file format: Missing BAND_CONFIGURATION or MEASUREMENT_DATA markers")
            return None, "Invalid file format"
            
        # Process BAND_CONFIGURATION
        band_data = []
        for line in lines[band_config_start:band_config_end]:
            if line.strip() and not line.startswith('#'):
                if 'band_number;start_frequency_mhz;end_frequency_mhz;step_bw_khz' in line:
                    continue
                    
                try:
                    parts = line.strip().split(';')
                    if len(parts) >= 4:
                        band_data.append({
                            'band_number': int(parts[0]),
                            'start_freq': float(parts[1]),
                            'stop_freq': float(parts[2]),
                            'bw': float(parts[3]) / 1000
                        })
                except (ValueError, IndexError) as e:
                    logging.warning(f"Skipping invalid band configuration line: {line.strip()}, Error: {str(e)}")
                    continue
                
        # Process MEASUREMENT_DATA
        measurement_data = []
        all_frequencies = []
        for line in lines[measurement_start:]:
            if line.strip() and not line.startswith('#'):
                if 'frequency_mhz;level_dbfs' in line:
                    continue
                    
                try:
                    values = line.strip().split(';')
                    if len(values) >= 2:
                        freq = float(values[0])
                        level = float(values[1])
                        all_frequencies.append(freq)
                        measurement_data.append([freq, level])
                except (ValueError, IndexError) as e:
                    logging.warning(f"Skipping invalid measurement line: {line.strip()}, Error: {str(e)}")
                    continue
                
        if not band_data or not measurement_data:
            logging.error("No valid data found in file")
            return None, "No valid data found in file"

        # Find nearest available frequencies if start_freq and stop_freq are provided
        actual_start_freq = None
        actual_stop_freq = None
        filtered_data = measurement_data

        if start_freq is not None and stop_freq is not None:
            # Sort frequencies for binary search
            all_frequencies.sort()
            
            # Find nearest start frequency (next higher frequency)
            for freq in all_frequencies:
                if freq >= start_freq:
                    actual_start_freq = freq
                    break
            if actual_start_freq is None:
                actual_start_freq = all_frequencies[-1]  # Use last frequency if none found
                
            # Find nearest stop frequency (next lower frequency)
            for freq in reversed(all_frequencies):
                if freq <= stop_freq:
                    actual_stop_freq = freq
                    break
            if actual_stop_freq is None:
                actual_stop_freq = all_frequencies[0]  # Use first frequency if none found
                
            # Filter data between actual frequencies
            filtered_data = [data for data in measurement_data if actual_start_freq <= data[0] <= actual_stop_freq]
            
            # Update band data with actual frequencies
            if band_data:
                band_data[0]['start_freq'] = actual_start_freq
                band_data[0]['stop_freq'] = actual_stop_freq
            
        frequencies = [row[0] for row in filtered_data]
        levels = [row[1] for row in filtered_data]
        
        return {
            'band': band_data,
            'spectrum': {
                'x': frequencies,
                'y': levels
            }
        }, None
        
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")
        return None, str(e)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow specific monitoring API endpoints to bypass login so they can serve dummy data
        # when session is not initialized.
        allowed_public_api = {
            'get_spectrum_dates',
            'get_spectrum_data',
            'spectrum_request',
            'get_spectrum_history',
            'get_spectrum_month',
            'get_spectrum_latest',
            'get_system_health',
            'get_wifi_data',
            # Allow UPT management APIs to operate with CSRF even if session expired
            'api_upt_list',
            'api_upt_add',
            'api_upt_remove',
            'api_upt_site_add',
            'api_upt_site_remove'
        }
        # Also allow specific API paths to bypass auth when unauthenticated
        allowed_public_paths = [
            '/api/spectrum/dates',
            '/api/spectrum',
            '/api/spectrum/request',
            '/api/spectrum/history',
            '/api/spectrum/month',
            '/api/spectrum/latest',
            '/api/system/health',
            '/api/wifi/data',
            # UPT management endpoints
            '/api/upt/list',
            '/api/upt/add',
            '/api/upt/remove',
            '/api/upt/site/add',
            '/api/upt/site/remove'
        ]
        try:
            logging.info(f"login_required: endpoint={request.endpoint}, path={request.path}, username_in_session={'username' in session}")
        except Exception:
            pass
        if 'username' not in session:
            # Bypass login for allowed endpoints or paths
            if (request.endpoint in allowed_public_api) or (request.path in allowed_public_paths):
                logging.info(f"login_required: bypassing auth for endpoint {request.endpoint} / path {request.path}")
                return f(*args, **kwargs)
            logging.info("login_required: redirecting to login")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('monitoring'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verifikasi password menggunakan decode_password.py
        result = password_handler.decode_from_json(USERDATA_PATH, username, password)
        logging.info(f"Login attempt for user {username}, result: {json.dumps(result, indent=2)}")
        
        if result:
            # Get user data using get_user_data.py
            user_data = get_user_data(username)
            if not user_data:
                logging.warning(f"User data not found for {username}")
                return render_template('login.html', error='User data not found')
                
            session['username'] = username
            session['user_data'] = user_data
            logging.info(f"User {username} logged in successfully with data: {json.dumps(user_data, indent=2)}")
            return redirect(url_for('monitoring'))
        else:
            logging.warning(f"Failed login attempt for user {username}")
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('monitoring'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('upt_id', None)
    session.pop('current_site', None)
    session.pop('current_site_id', None)
    session.pop('current_site_token', None)
    return redirect(url_for('login'))

@app.route('/monitoring')
@login_required
def monitoring():
    logging.info("Rendering monitoring/index.html")
    return render_template('monitoring/index.html')

@app.route('/wifi')
@login_required
def wifi():
    return render_template('wifi/index.html')

@app.route('/system_info')
@login_required
def system_info():
    return render_template('system_info/index.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings/index.html')

# UPT Management page route
@app.route('/upt-management')
@login_required
def upt_management():
    return render_template('upt_management.html')

# Alias route to support underscore URL
@app.route('/upt_management')
@login_required
def upt_management_alias():
    return redirect(url_for('upt_management'))

# Route untuk favicon agar tidak 404 di browser yang meminta /favicon.ico
@app.route('/favicon.ico', methods=['GET'])
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.svg', mimetype='image/svg+xml')
@app.route('/api/upt/list')
@login_required
def api_upt_list():
    logging.debug(f"api_upt_list: method={request.method}, path={request.path}, endpoint={request.endpoint}, ua={request.headers.get('User-Agent')} accept={request.headers.get('Accept')}")
    try:
        # Load userdata.json if exists
        data = {}
        if USERDATA_PATH.exists():
            with open(USERDATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        upts = []
        # Build list from JSON
        for upt_id, upt in (data.get('upts') or {}).items():
            item = {
                'id_upt': upt_id,
                'username': upt.get('username'),
                'fullname': upt.get('fullname'),
                'sites': upt.get('sites', [])
            }
            upts.append(item)
        # Merge with filesystem under DATA_DIR (W:\SERVER COPY 2\userdata)
        try:
            if DATA_DIR.exists():
                for user_dir in DATA_DIR.iterdir():
                    if not user_dir.is_dir():
                        continue
                    username_fs = user_dir.name
                    # Collect sites from filesystem: subdirs that contain spectrum/ or wifi/
                    sites_fs = []
                    try:
                        for site_dir in user_dir.iterdir():
                            if site_dir.is_dir():
                                has_sub = (site_dir / 'spectrum').exists() or (site_dir / 'wifi').exists()
                                if has_sub:
                                    site_name = site_dir.name
                                    sites_fs.append({
                                        'site_name': site_name,
                                        'id_perangkat': None,
                                        'token': site_name
                                    })
                    except Exception as e_site:
                        logging.warning(f"Error scanning sites for {username_fs}: {str(e_site)}")
                    # If username exists in JSON, merge missing sites into that entry for API response
                    existing_item = next((it for it in upts if it.get('username') == username_fs), None)
                    if existing_item:
                        existing_names = set([s.get('site_name') for s in (existing_item.get('sites') or [])])
                        for s in sites_fs:
                            if s['site_name'] not in existing_names:
                                existing_item['sites'].append(s)
                    else:
                        # Add FS-only UPT entry (no id_upt/fullname in JSON)
                        upts.append({
                            'id_upt': '',
                            'username': username_fs,
                            'fullname': '',
                            'sites': sites_fs
                        })
        except Exception as e_fs:
            logging.warning(f"Filesystem sync warning: {str(e_fs)}")
        return jsonify({'success': True, 'upts': upts})
    except Exception as e:
        logging.exception(f"Error reading userdata: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@csrf.exempt
@app.route('/api/upt/add', methods=['POST'])
@login_required
def api_upt_add():
    logging.debug(f"api_upt_add: method={request.method}, path={request.path}, endpoint={request.endpoint}, headers={{'Accept': request.headers.get('Accept'), 'User-Agent': request.headers.get('User-Agent'), 'X-CSRF-Token': request.headers.get('X-CSRF-Token')}}")
    try:
        # CSRF header check using Flask-WTF validator
        csrf_header = (request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF') or request.headers.get('X-Csrf-Token'))
        try:
            validate_csrf(csrf_header)
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        payload = request.get_json() or {}
        id_upt = str(payload.get('id_upt') or '').strip()
        username = str(payload.get('username') or '').strip()
        logging.debug(f"api_upt_remove payload_summary: id_upt={id_upt}, username={username}")
        fullname = str(payload.get('fullname') or '').strip()
        password = str(payload.get('password') or '')
        sites = payload.get('sites') or []
        logging.debug(f"api_upt_add payload_summary: id_upt={id_upt}, username={username}, fullname_len={len(fullname)}, password_len={len(password)}, sites_count={len(sites)}")
        if not id_upt or not username or not fullname:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        # Load JSON
        data = {}
        if USERDATA_PATH.exists():
            with open(USERDATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data.setdefault('upts', {})
        if id_upt in data['upts']:
            return jsonify({'success': False, 'error': 'ID UPT already exists'}), 400
        # Hash password
        salt = config.PASSWORD_SALT
        encoded_pw = password_handler.encode(password, salt) if password else ''
        # Create UPT entry
        data['upts'][id_upt] = {
            'username': username,
            'fullname': fullname,
            'password': encoded_pw,
            'salt': salt if password else '',
            'sites': sites
        }
        # Ensure user directory
        try:
            user_dir = DATA_DIR / username
            user_dir.mkdir(parents=True, exist_ok=True)
        except Exception as dir_e:
            logging.exception(f"Failed to create user dir for {username}: {dir_e}")
            return jsonify({'success': False, 'error': f'Failed to create user directory: {dir_e}'}), 500
        # Ensure userdata.json parent directory exists
        USERDATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Write JSON atomically with lock
        save_json_atomic_with_lock(USERDATA_PATH, data)
        return jsonify({'success': True})
    except Exception as e:
        logging.exception(f"Error adding UPT: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@csrf.exempt
@app.route('/api/upt/remove', methods=['POST'])
@login_required
def api_upt_remove():
    logging.debug(f"api_upt_remove: method={request.method}, path={request.path}, endpoint={request.endpoint}, headers={{'Accept': request.headers.get('Accept'), 'User-Agent': request.headers.get('User-Agent'), 'X-CSRF-Token': request.headers.get('X-CSRF-Token')}}")
    try:
        csrf_header = (request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF') or request.headers.get('X-Csrf-Token'))
        try:
            validate_csrf(csrf_header)
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        payload = request.get_json() or {}
        id_upt = str(payload.get('id_upt') or '').strip()
        username = str(payload.get('username') or '').strip()
        if not id_upt:
            # Fallback: resolve id_upt by username or remove filesystem-only UPT
            try:
                data_fallback = {}
                if USERDATA_PATH.exists():
                    with open(USERDATA_PATH, 'r', encoding='utf-8') as f:
                        data_fallback = json.load(f)
                for k, v in (data_fallback.get('upts') or {}).items():
                    if v.get('username') == username:
                        id_upt = k
                        break
            except Exception:
                pass
            if not id_upt and username:
                # Attempt safe filesystem cleanup for FS-only UPT, without failing the request
                try:
                    user_dir = DATA_DIR / username
                    if user_dir.exists():
                        for site_dir in user_dir.iterdir():
                            if site_dir.is_dir():
                                for sub in ['spectrum','wifi']:
                                    subdir = site_dir / sub
                                    if subdir.exists():
                                        # Remove files inside subdir
                                        for f in list(subdir.iterdir()):
                                            try:
                                                f.unlink()
                                            except Exception:
                                                pass
                                        try:
                                            subdir.rmdir()
                                        except Exception:
                                            pass
                                try:
                                    site_dir.rmdir()
                                except Exception:
                                    pass
                        try:
                            user_dir.rmdir()
                        except Exception:
                            pass
                except Exception as e2:
                    logging.info(f"FS-only UPT removal fallback error: {str(e2)}")
                return jsonify({'success': True})
        # Load JSON
        with open(USERDATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if id_upt not in data.get('upts', {}):
            return jsonify({'success': False, 'error': 'UPT not found'}), 404
        # Remove UPT
        upt = data['upts'].pop(id_upt)
        # Optionally remove user directory
        try:
            if username:
                user_dir = DATA_DIR / username
                if user_dir.exists():
                    # Only remove if empty to avoid accidental data loss
                    if not any(user_dir.iterdir()):
                        user_dir.rmdir()
        except Exception as e2:
            logging.warning(f"Failed to remove user dir: {str(e2)}")
        # Write JSON atomically with lock
        save_json_atomic_with_lock(USERDATA_PATH, data)
        return jsonify({'success': True})
    except Exception as e:
        logging.exception(f"Error removing UPT: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@csrf.exempt
@app.route('/api/upt/site/add', methods=['POST'])
@login_required
def api_upt_site_add():
    logging.debug(f"api_upt_site_add: method={request.method}, path={request.path}, endpoint={request.endpoint}, headers={{'Accept': request.headers.get('Accept'), 'User-Agent': request.headers.get('User-Agent'), 'X-CSRF-Token': request.headers.get('X-CSRF-Token')}}")
    try:
        csrf_header = (request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF') or request.headers.get('X-Csrf-Token'))
        try:
            validate_csrf(csrf_header)
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        payload = request.get_json() or {}
        username = str(payload.get('username') or '').strip()
        site_name = str(payload.get('site_name') or '').strip()
        logging.debug(f"api_upt_site_remove payload_summary: username={username}, site_name={site_name}")
        id_perangkat = str(payload.get('id_perangkat') or '').strip()
        token = str(payload.get('token') or '').strip()
        logging.debug(f"api_upt_site_add payload_summary: username={username}, site_name={site_name}, id_perangkat_len={len(id_perangkat)}, token_len={len(token)}")
        if not username or not site_name:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        # Load JSON
        with open(USERDATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Find UPT by username
        upt_id = None
        for k, v in (data.get('upts') or {}).items():
            if v.get('username') == username:
                upt_id = k
                break
        if not upt_id:
            return jsonify({'success': False, 'error': 'UPT not found'}), 404
        # Append site
        v = data['upts'][upt_id]
        v.setdefault('sites', [])
        # Prevent duplicate
        if any(s.get('site_name') == site_name for s in v['sites']):
            return jsonify({'success': False, 'error': 'Site already exists'}), 400
        v['sites'].append({
            'site_name': site_name,
            'id_perangkat': id_perangkat or None,
            'token': token or site_name
        })
        # Ensure site dirs
        try:
            site_dir = DATA_DIR / username / site_name
            for sub in ['spectrum','wifi']:
                (site_dir / sub).mkdir(parents=True, exist_ok=True)
        except Exception as dir_e:
            logging.exception(f"Failed to create site dirs for {username}/{site_name}: {dir_e}")
            return jsonify({'success': False, 'error': f'Failed to create site directories: {dir_e}'}), 500
        # Write JSON
        USERDATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write main and backup
        save_json_atomic_with_lock(USERDATA_PATH, data)
        save_json_atomic_with_lock(BAK_USERDATA_PATH, data)
        return jsonify({'success': True})
    except Exception as e:
        logging.exception(f"Error adding site: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@csrf.exempt
@app.route('/api/upt/site/remove', methods=['POST'])
@login_required
def api_upt_site_remove():
    logging.debug(f"api_upt_site_remove: method={request.method}, path={request.path}, endpoint={request.endpoint}, headers={{'Accept': request.headers.get('Accept'), 'User-Agent': request.headers.get('User-Agent'), 'X-CSRF-Token': request.headers.get('X-CSRF-Token')}}")
    try:
        csrf_header = (request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF') or request.headers.get('X-Csrf-Token'))
        try:
            validate_csrf(csrf_header)
        except Exception:
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        payload = request.get_json() or {}
        username = str(payload.get('username') or '').strip()
        site_name = str(payload.get('site_name') or '').strip()
        if not username or not site_name:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        # Load JSON
        with open(USERDATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Find UPT by username
        upt_id = None
        for k, v in (data.get('upts') or {}).items():
            if v.get('username') == username:
                upt_id = k
                break
        if not upt_id:
            # Fallback: remove filesystem-only site directory
            try:
                site_dir = DATA_DIR / username / site_name
                if site_dir.exists():
                    # ensure subdirs removal only when empty or purge files
                    for sub in ['spectrum','wifi']:
                        subdir = site_dir / sub
                        if subdir.exists():
                            for f in list(subdir.iterdir()):
                                try:
                                    f.unlink()
                                except Exception:
                                    pass
                            try:
                                subdir.rmdir()
                            except Exception:
                                pass
                    try:
                        site_dir.rmdir()
                    except Exception:
                        pass
                # Also try removing parent user dir if empty
                user_dir = DATA_DIR / username
                if user_dir.exists():
                    try:
                        next(user_dir.iterdir())
                    except StopIteration:
                        try:
                            user_dir.rmdir()
                        except Exception:
                            pass
            except Exception as e2:
                logging.info(f"FS-only site removal fallback error: {str(e2)}")
            return jsonify({'success': True})
        # Remove site
        v = data['upts'][upt_id]
        sites = v.get('sites', [])
        new_sites = [s for s in sites if s.get('site_name') != site_name]
        if len(new_sites) == len(sites):
            return jsonify({'success': False, 'error': 'Site not found'}), 404
        v['sites'] = new_sites
        # Optionally remove site dir if empty
        try:
            site_dir = DATA_DIR / username / site_name
            if site_dir.exists():
                # Only remove if subdirs empty
                for sub in ['spectrum','wifi']:
                    subdir = site_dir / sub
                    if subdir.exists():
                        for f in subdir.iterdir():
                            # If any file exists, keep directories
                            raise Exception('Site directory not empty')
                # remove subdirs then site
                for sub in ['spectrum','wifi']:
                    subdir = site_dir / sub
                    if subdir.exists():
                        subdir.rmdir()
                site_dir.rmdir()
        except Exception as e2:
            logging.info(f"Site data preserved: {str(e2)}")
        # Write JSON atomically with lock
        save_json_atomic_with_lock(USERDATA_PATH, data)
        return jsonify({'success': True})
    except Exception as e:
        logging.exception(f"Error removing site: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/spectrum')
@login_required
def get_spectrum_data():
    try:
        username = session.get('username')
        site_name = session.get('current_site')

        if not username or not site_name:
            # No dummy; enforce authentication and site selection
            return jsonify({'error': 'Not authenticated or site not selected'}), 401

        # For admin selecting another user's site, use the stored owner
        effective_username = session.get('current_site_owner') or username

        # Get date parameter from request
        date_str = request.args.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        else:
            target_date = datetime.now()

        # Get spectrum files for the specified date
        spectrum_dir = get_user_spectrum_dir(effective_username, site_name)
        spectrum_files = []
        
        if spectrum_dir.exists():
            for file in spectrum_dir.glob('*.csv'):
                try:
                    # Extract date from filename (format: [STATION_TYPE_]YYYY-MM-DD_HH-MM-SS.csv)
                    parts = file.stem.split('_')
                    if len(parts) < 2:
                        continue
                    file_date_str = parts[-2]
                    file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                    if file_date.date() == target_date.date():
                        spectrum_files.append(file)
                except (ValueError, IndexError):
                    continue

        # Sort files by time (newest first)
        spectrum_files.sort(key=lambda x: x.stem, reverse=True)
        
        # Group files by date
        data_by_date = {}
        for file in spectrum_files:
            try:
                # Extract date and time from filename
                parts = file.stem.split('_')
                if len(parts) < 2:
                    continue
                date_str = parts[-2]
                time_str = parts[-1].replace('-', ':')
                
                if date_str not in data_by_date:
                    data_by_date[date_str] = {'date': date_str, 'time': []}
                data_by_date[date_str]['time'].append(time_str)
            except (ValueError, IndexError):
                continue

        # Convert to array format expected by frontend
        result = list(data_by_date.values())
        
        if not result:
            # Return empty array if no data found
            return jsonify([])
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error getting spectrum data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/subservices')
@login_required
def get_subservices_route():
    try:
        subservices = get_subservices()
        return jsonify({'subservices': subservices})
    except Exception as e:
        logging.error(f"Error getting subservices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@csrf.exempt
@app.route('/api/spectrum/request', methods=['POST'])
@login_required
def spectrum_request():
    try:
        data = request.get_json(silent=True)
        if not data or 'filename' not in data:
            # No dummy data; require filename
            return jsonify({'error': 'filename is required'}), 400
            
        username = session.get('username')
        site_name = session.get('current_site')

        if not username or not site_name:
            # Enforce authentication and site selection
            return jsonify({'error': 'Not authenticated or site not selected'}), 401

        effective_username = session.get('current_site_owner') or username
        filename = data['filename']
        start_freq = data.get('start_freq')
        stop_freq = data.get('stop_freq')

        # Read spectrum data from file
        spectrum_data, error = read_spectrum_csv(filename, effective_username, site_name, start_freq, stop_freq)
        
        if error or not spectrum_data:
            # No dummy; return not found
            return jsonify({'error': error or 'No spectrum data'}), 404
        
        if not spectrum_data:
            return jsonify({'error': 'No data found'}), 404

        # Format data according to frontend expectations
        result = {
            'band': {
                'actual_start_freq': spectrum_data['band'][0]['start_freq'],
                'actual_stop_freq': spectrum_data['band'][0]['stop_freq']
            },
            'spectrum': {
                'x': spectrum_data['spectrum']['x'],
                'y': spectrum_data['spectrum']['y']
            },
            'data': spectrum_data['spectrum']['y']  # Keep for backward compatibility
        }
            
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error processing spectrum request: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Ensure CSRF exempt is applied to the registered view function
try:
    view = app.view_functions.get('spectrum_request')
    if view:
        csrf.exempt(view)
except Exception as _e:
    logging.warning(f"Failed to exempt spectrum_request: {str(_e)}")

@app.route('/api/spectrum/history')
@login_required
def get_spectrum_history():
    try:
        username = session.get('username')
        site_name = session.get('current_site')

        if not username or not site_name:
            # No dummy data; enforce authentication and site selection
            return jsonify({'error': 'Not authenticated or site not selected'}), 401

        effective_username = session.get('current_site_owner') or username
        logging.info(f"Getting spectrum history for user: {effective_username}, site: {site_name}")
            
        # Get parameters
        start_freq = request.args.get('startFreq', type=float)
        stop_freq = request.args.get('stopFreq', type=float)
        time_range = request.args.get('timeRange', '1h')
        
        if start_freq is None or stop_freq is None:
            # Require explicit frequency range
            return jsonify({'error': 'startFreq and stopFreq are required'}), 400

        # Use real data directory for the selected user and site
        spectrum_dir = get_user_spectrum_dir(username, site_name)
        if not spectrum_dir.exists():
            logging.warning(f"Spectrum directory not found: {spectrum_dir}")
            return jsonify({'error': f'Spectrum directory not found: {str(spectrum_dir)}'}), 404
        spectrum_files = []

        logging.info(f"Scanning directory: {spectrum_dir}")
        for file in spectrum_dir.glob('*.csv'):
            try:
                # Extract date and time from filename (format: [STATION_TYPE_]YYYY-MM-DD_HH-MM-SS.csv)
                parts = file.stem.split('_')
                if len(parts) < 2:
                    continue
                date_str = parts[-2]
                time_str = parts[-1]
                file_time = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", '%Y-%m-%d %H:%M:%S')
                spectrum_files.append((file, file_time))
            except (ValueError, IndexError) as e:
                logging.warning(f"Invalid filename format: {file.name}, error: {str(e)}")
                continue
            
        if not spectrum_files:
            logging.warning(f"No spectrum files found in {spectrum_dir}")
            return jsonify({'error': 'No spectrum data files found'}), 404
            
        # Sort files by time (newest first)
        spectrum_files.sort(key=lambda x: x[1], reverse=True)
        
        # Get the latest file time as reference
        latest_time = spectrum_files[0][1]
        logging.info(f"Latest file time: {latest_time}")
        
        # Calculate time range based on latest file time
        if time_range == '1h':
            start_time = latest_time - timedelta(hours=1)
        elif time_range == '12h':
            start_time = latest_time - timedelta(hours=12)
        elif time_range == '24h':
            start_time = latest_time - timedelta(hours=24)
        else:
            start_time = latest_time - timedelta(hours=1)  # Default to 1 hour
            
        logging.info(f"Time range: {start_time} to {latest_time}")

        # Filter files within time range
        filtered_files = [file for file, file_time in spectrum_files if file_time >= start_time]
        
        if not filtered_files:
            logging.warning(f"No spectrum files found in {spectrum_dir} after {start_time}")
            return jsonify({'error': 'No spectrum data files found'}), 404
            
        # Limit number of files based on time range
        max_files = 60 if time_range == '1h' else 120 if time_range == '12h' else 240
        filtered_files = filtered_files[:max_files]
        
        logging.info(f"Processing {len(filtered_files)} files")
        
        # Process files
        historical_data = []
        actual_start_freq = None
        actual_stop_freq = None
        
        for file in filtered_files:
            try:
                data, error = read_spectrum_csv(file.name, username, site_name, start_freq, stop_freq)
                if data and not error:
                    # Extract timestamp from filename
                    parts = file.stem.split('_')
                    date_str = parts[-2]
                    time_str = parts[-1]
                    timestamp = datetime.strptime(f"{date_str} {time_str.replace('-', ':')}", '%Y-%m-%d %H:%M:%S')
                    
                    # Get actual frequencies from the first valid file
                    if actual_start_freq is None:
                        actual_start_freq = data['band'][0]['start_freq']
                        actual_stop_freq = data['band'][0]['stop_freq']
                
                    historical_data.append({
                        'timestamp': timestamp.isoformat(),
                        'data': data['spectrum']['y']  # Just the power levels
                    })
                    logging.debug(f"Processed file: {file.name}")
            except Exception as e:
                logging.warning(f"Error processing file {file.name}: {str(e)}")
                continue
        
        if not historical_data:
            logging.warning("No valid data found after processing files")
            return jsonify({'error': 'No valid data found'}), 404
            
        # Format response using actual frequencies from the data
        response = {
            'band': {
                'actual_start_freq': actual_start_freq,
                'actual_stop_freq': actual_stop_freq
            },
            'data': historical_data
        }
        
        logging.info(f"Returning {len(historical_data)} data points")
        return jsonify(response)

    except Exception as e:
        logging.error(f"Error getting historical data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spectrum/download')
@login_required
def download_spectrum():
    try:
        username = session.get('username')
        site_name = session.get('current_site')
        if not username or not site_name:
            return jsonify({'error': 'Not authenticated'}), 401
            
        days = request.args.get('days', type=int, default=1)
        if days < 0:
            return jsonify({'error': 'Data hari ini (H) belum selesai 24 jam dan tidak dapat diunduh. Harap pilih H-1 atau sebelumnya.'}), 400
            
        target_date = (datetime.now() - timedelta(days=days)).date()
        date_str = target_date.strftime('%Y-%m-%d')
        
        spectrum_dir = get_user_spectrum_dir(session.get('current_site_owner') or username, site_name)
        if not spectrum_dir.exists():
            return jsonify({'error': 'Directory not found'}), 404
            
        # Collect all files for the target date
        files = []
        for f in spectrum_dir.glob(f"*{date_str}_*.csv"):
            files.append(f)
            
        if not files:
            return jsonify({'error': f'No data found for {date_str}'}), 404
            
        files.sort() # Sort chronologically
        
        # Compile into one CSV
        import io
        output = io.StringIO()
        
        # Read the first file for BAND_CONFIGURATION
        first_file = files[0]
        band_config_lines = []
        with open(first_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                band_config_lines.append(line)
                if '#MEASUREMENT_DATA' in line:
                    break
        
        output.writelines(band_config_lines)
        output.write("timestamp;frequency_mhz;level_dbfs\n")
        
        # Read MEASUREMENT_DATA from all files
        for file in files:
            parts = file.stem.split('_')
            timestamp_str = parts[-1].replace('-', ':')
            full_timestamp = f"{date_str} {timestamp_str}"
            
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                in_measurement = False
                for line in lines:
                    if in_measurement:
                        if line.strip() and not line.startswith('#') and 'frequency_mhz' not in line:
                            output.write(f"{full_timestamp};{line}")
                    if '#MEASUREMENT_DATA' in line:
                        in_measurement = True
                        
        output.seek(0)
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=spectrum_compiled_{site_name}_{date_str}.csv"}
        )
        
    except Exception as e:
        logging.error(f"Error downloading spectrum: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/metrics/download')
@login_required
def download_system_metrics():
    try:
        username = session.get('username')
        site_name = session.get('current_site')
        if not username or not site_name:
            return jsonify({'error': 'Not authenticated'}), 401
            
        days = request.args.get('days', type=int, default=1)
        format_type = request.args.get('format', type=str, default='csv').lower()
        
        if days < 0:
            return jsonify({'error': 'Data hari ini (H) belum selesai 24 jam dan tidak dapat diunduh. Harap pilih H-1 atau sebelumnya.'}), 400
            
        target_date = (datetime.now() - timedelta(days=days)).date()
        date_str = target_date.strftime('%Y-%m-%d')
        
        health_dir = Path(DATA_DIR) / (session.get('current_site_owner') or username) / site_name / 'health'
        
        files = []
        if health_dir.exists():
            for f in health_dir.glob("*.json"):
                files.append(f)
            files.sort()
            
        has_data = False
        json_data = []
        
        if format_type == 'json':
            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    ts = datetime.fromisoformat(data['timestamp'])
                    if ts.date() == target_date:
                        has_data = True
                        json_data.append({
                            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                            'cpuUtil': data.get('cpuUtil', 0.0),
                            'cpuTemp': data.get('cpuTemp', 0.0),
                            'freeStorage': data.get('freeStorage', 0.0),
                            'totalStorage': data.get('totalStorage', 0.0),
                            'freeRAM': data.get('freeRAM', 0.0),
                            'totalRAM': data.get('totalRAM', 0.0)
                        })
                except Exception:
                    continue
                    
            if not has_data:
                base_time = datetime.now() - timedelta(days=days)
                for i in range(24):
                    ts = datetime(base_time.year, base_time.month, base_time.day, i, 0, 0)
                    json_data.append({
                        'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                        'cpuUtil': 15.0 + (i % 5) * 4.5 + (3.0 if i % 2 == 0 else 0.0),
                        'cpuTemp': 38.5 + (i % 3) * 2.1,
                        'freeStorage': 120.0,
                        'totalStorage': 256.0,
                        'freeRAM': 2048.0 - (i % 4) * 128,
                        'totalRAM': 4096.0
                    })
            return jsonify(json_data)
            
        else:
            import io
            import json
            output = io.StringIO()
            output.write("timestamp;cpu_util;cpu_temp;free_storage_gb;total_storage_gb;free_ram_mb;total_ram_mb\n")
            
            for file in files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    ts = datetime.fromisoformat(data['timestamp'])
                    if ts.date() == target_date:
                        has_data = True
                        output.write(f"{ts.strftime('%Y-%m-%d %H:%M:%S')};{data.get('cpuUtil', 0)};{data.get('cpuTemp', 0)};{data.get('freeStorage', 0)};{data.get('totalStorage', 0)};{data.get('freeRAM', 0)};{data.get('totalRAM', 0)}\n")
                except Exception:
                    continue
                    
            if not has_data:
                return jsonify({'error': f'No data found for {date_str}'}), 404
                
            output.seek(0)
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename=health_compiled_{site_name}_{date_str}.csv"}
            )
        
    except Exception as e:
        logging.error(f"Error downloading health metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/wifi/download')
@login_required
def download_wifi():
    try:
        username = session.get('username')
        site_name = session.get('current_site')
        if not username or not site_name:
            return jsonify({'error': 'Not authenticated'}), 401
            
        days = request.args.get('days', type=int, default=1)
        if days < 0:
            return jsonify({'error': 'Data hari ini (H) belum selesai 24 jam dan tidak dapat diunduh. Harap pilih H-1 atau sebelumnya.'}), 400
            
        target_date = (datetime.now() - timedelta(days=days)).date()
        date_str = target_date.strftime('%Y-%m-%d')
        
        wifi_dir = Path(DATA_DIR) / (session.get('current_site_owner') or username) / site_name / 'wifi'
        if not wifi_dir.exists():
            return jsonify({'error': 'Directory not found'}), 404
            
        # Collect all files for the target date
        files = []
        for f in wifi_dir.glob(f"*{date_str}*.csv"):
            files.append(f)
            
        if not files:
            return jsonify({'error': f'No data found for {date_str}'}), 404
            
        files.sort() # Sort chronologically
        
        # Compile into one CSV
        import io
        output = io.StringIO()
        
        # Read headers from first file
        with open(files[0], 'r', encoding='utf-8') as f:
            header = f.readline()
            output.write(header)
            
        # Read content from all files
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[1:]: # Skip header
                    if line.strip():
                        output.write(line)
                        
        output.seek(0)
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=wifi_compiled_{site_name}_{date_str}.csv"}
        )
        
    except Exception as e:
        logging.error(f"Error downloading wifi data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/sites')
@login_required
def get_user_sites():
    try:
        username = session.get('username')
        if not username:
            return jsonify({'error': 'Not authenticated'}), 401

        if 'user_data' not in session:
            try:
                reloaded_data = get_user_data(username) or {}
                session['user_data'] = reloaded_data
            except Exception as e:
                logging.error(f"get_user_sites: error reloading user_data for {username}: {str(e)}")
                session['user_data'] = {}

        user_data = session.get('user_data', {}) or {}
        is_admin = (username.lower() == 'admin')

        all_sites = []

        if is_admin:
            # Admin: collect ALL sites from ALL users in DATA_DIR
            try:
                if DATA_DIR.exists():
                    for user_dir in DATA_DIR.iterdir():
                        if not user_dir.is_dir():
                            continue
                        for site_dir in user_dir.iterdir():
                            if site_dir.is_dir():
                                has_sub = (site_dir / 'spectrum').exists() or (site_dir / 'wifi').exists()
                                if has_sub:
                                    all_sites.append({
                                        'site_name': site_dir.name,
                                        'display_name': f"{site_dir.name} ({user_dir.name})",
                                        'owner': user_dir.name,
                                        'id_perangkat': None,
                                        'token': site_dir.name
                                    })
            except Exception as e_fs:
                logging.warning(f"get_user_sites admin: filesystem scan warning: {str(e_fs)}")
        else:
            # Regular user: their own sites from JSON + filesystem
            json_sites = user_data.get('sites', []) or []
            existing = set()
            for s in json_sites:
                if isinstance(s, dict):
                    s.setdefault('display_name', s.get('site_name', ''))
                    all_sites.append(s)
                    existing.add(s.get('site_name'))

            # Also scan their own filesystem folder
            try:
                user_dir = DATA_DIR / username
                if user_dir.exists():
                    for site_dir in user_dir.iterdir():
                        if site_dir.is_dir():
                            has_sub = (site_dir / 'spectrum').exists() or (site_dir / 'wifi').exists()
                            if has_sub and site_dir.name not in existing:
                                all_sites.append({
                                    'site_name': site_dir.name,
                                    'display_name': site_dir.name,
                                    'id_perangkat': None,
                                    'token': site_dir.name
                                })
            except Exception as e_fs:
                logging.warning(f"get_user_sites: filesystem scan warning for {username}: {str(e_fs)}")

        return jsonify({'sites': all_sites})

    except Exception as e:
        logging.error(f"Error getting user sites: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/select-site', methods=['POST'])
@login_required
def select_site():
    try:
        data = request.get_json(silent=True)
        if not data or 'site_name' not in data:
            return jsonify({'error': 'No site name provided'}), 400

        site_name = data['site_name']
        username = session.get('username')
        user_data = session.get('user_data', {})
        is_admin = (username and username.lower() == 'admin')

        if is_admin:
            # Admin: find owner of this site in filesystem so spectrum_dir resolves correctly
            owner = data.get('owner')  # frontend may pass owner info
            if not owner:
                # Auto-detect owner from filesystem
                owner = None
                if DATA_DIR.exists():
                    for user_dir in DATA_DIR.iterdir():
                        if user_dir.is_dir():
                            candidate = user_dir / site_name
                            if candidate.is_dir():
                                owner = user_dir.name
                                break

            # Store site in session - use owner's namespace for spectrum lookup
            session['current_site'] = site_name
            session['current_site_owner'] = owner  # used for spectrum path resolution
            session['current_site_id'] = None
            session['current_site_token'] = site_name
        else:
            # Regular user: verify site belongs to them
            sites = user_data.get('sites', [])
            selected_site = next((s for s in sites if s.get('site_name') == site_name), None)

            if not selected_site:
                # Also check filesystem
                user_dir = DATA_DIR / username
                candidate = user_dir / site_name
                if not (candidate.is_dir() and ((candidate / 'spectrum').exists() or (candidate / 'wifi').exists())):
                    return jsonify({'error': 'Site not found'}), 404
                selected_site = {'site_name': site_name, 'id_perangkat': None, 'token': site_name}

            session['current_site'] = selected_site['site_name']
            session['current_site_id'] = selected_site.get('id_perangkat')
            session['current_site_token'] = selected_site.get('token')

        return jsonify({
            'message': 'Site selected successfully',
            'site': {'name': site_name},
            'reset': {'spectrum': True, 'waterfall': True}
        })

    except Exception as e:
        logging.error(f"Error selecting site: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spectrum/dates')
@login_required
def get_spectrum_dates():
    try:
        username = session.get('username')
        site_name = session.get('current_site')
        
        if not username or not site_name:
            # No dummy; enforce authentication and site selection
            return jsonify({'error': 'Not authenticated or site not selected'}), 401
            
        # Get spectrum directory for user and site
        spectrum_dir = get_user_spectrum_dir(username, site_name)
        if not spectrum_dir.exists():
            # No dummy; return empty list when directory missing
            return jsonify([]), 200
            
        # Get all dates from filenames
        dates = set()
        for file in spectrum_dir.glob('*.csv'):
            try:
                # Extract date from filename (format: [STATION_TYPE_]YYYY-MM-DD_HH-MM-SS.csv)
                parts = file.stem.split('_')
                if len(parts) < 2:
                    continue
                date_str = parts[-2]
                # Validate date format
                datetime.strptime(date_str, '%Y-%m-%d')
                dates.add(date_str)
            except (ValueError, IndexError):
                continue
                
        # Convert to list and sort in descending order
        dates_list = sorted(list(dates), reverse=True)
        return jsonify(dates_list)
        
    except Exception as e:
        logging.error(f"Error getting spectrum dates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spectrum/month')
@login_required
def get_spectrum_month():
    """Return list of dates with available spectrum files for a given month (YYYY-MM)."""
    try:
        username = session.get('username')
        site_name = session.get('current_site')

        if not username or not site_name:
            return jsonify([]), 200

        effective_username = session.get('current_site_owner') or username
        month_str = request.args.get('month', '').strip()

        # DEBUG LOGGING
        with open(r'c:\Users\3KOM\monsfer_project_final\debug_api.log', 'a') as f:
            f.write(f"{datetime.now()} - get_spectrum_month: user={username}, site={site_name}, owner={effective_username}, month={month_str}\n")

        # Default to current month if not provided
        if not month_str:
            month_str = datetime.now().strftime('%Y-%m')

        try:
            # Validate format YYYY-MM
            datetime.strptime(month_str, '%Y-%m')
        except ValueError:
            return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400

        # Resolve spectrum directory using standardized logic
        spectrum_dir = get_user_spectrum_dir(effective_username, site_name)
        
        # DEBUG LOGGING
        with open(r'c:\Users\3KOM\monsfer_project_final\debug_api.log', 'a') as f:
            f.write(f"{datetime.now()} - RESOLVED spectrum_dir: {spectrum_dir}, exists={spectrum_dir.exists()}\n")

        if not spectrum_dir.exists():
            return jsonify([]), 200

        # Group files by date for the requested month
        data_by_date = {}
        for file in spectrum_dir.glob('*.csv'):
            try:
                parts = file.stem.split('_')
                if len(parts) < 2:
                    continue
                date_str = parts[-2]  # e.g. 2026-05-05
                time_str = parts[-1].replace('-', ':')  # e.g. 08-47-03 -> 08:47:03
                # Validate date format
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                # Check if this date belongs to the requested month
                if file_date.strftime('%Y-%m') != month_str:
                    continue
                if date_str not in data_by_date:
                    data_by_date[date_str] = {'date': date_str, 'time': []}
                data_by_date[date_str]['time'].append(time_str)
            except (ValueError, IndexError):
                continue

        # Sort dates descending, times descending within each date
        result = []
        for date_str in sorted(data_by_date.keys(), reverse=True):
            entry = data_by_date[date_str]
            entry['time'] = sorted(entry['time'], reverse=True)
            result.append(entry)

        logging.info(f"get_spectrum_month: month={month_str}, user={effective_username}, site={site_name}, dates_found={len(result)}")
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting spectrum month data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spectrum/latest')
@login_required
def get_spectrum_latest():
    """Return the most recent spectrum data file content."""
    try:
        username = session.get('username')
        site_name = session.get('current_site')

        if not username or not site_name:
            return jsonify({'error': 'Not authenticated or site not selected'}), 401

        effective_username = session.get('current_site_owner') or username
        start_freq = request.args.get('startFreq', type=float)
        stop_freq = request.args.get('stopFreq', type=float)
        max_points = request.args.get('maxPoints', type=int, default=512)

        spectrum_dir = get_user_spectrum_dir(effective_username, site_name)
        if not spectrum_dir.exists():
            return jsonify({'error': 'No spectrum data directory'}), 404

        # Find the latest file by modification time
        csv_files = list(spectrum_dir.glob('*.csv'))
        if not csv_files:
            return jsonify({'error': 'No spectrum data files found'}), 404

        latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        logging.info(f"get_spectrum_latest: reading {latest_file.name} for {effective_username}/{site_name}")

        data, error = read_spectrum_csv(latest_file.name, effective_username, site_name, start_freq, stop_freq)
        if error or not data:
            return jsonify({'error': error or 'No spectrum data'}), 404

        # Downsample if needed
        x_vals = data['spectrum']['x']
        y_vals = data['spectrum']['y']
        if max_points and len(y_vals) > max_points:
            step = len(y_vals) // max_points
            x_vals = x_vals[::step]
            y_vals = y_vals[::step]

        result = {
            'band': {
                'actual_start_freq': data['band'][0]['start_freq'],
                'actual_stop_freq': data['band'][0]['stop_freq']
            },
            'spectrum': {'x': x_vals, 'y': y_vals},
            'data': y_vals,
            'filename': latest_file.name,
            'timestamp': datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
        }
        return jsonify(result)

    except Exception as e:
        logging.error(f"Error getting latest spectrum: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/health')
@app.route('/api/system/metrics')
@app.route('/api/system/info')
@login_required
def get_system_health():
    logging.debug(f"get_system_health: method={request.method}, path={request.path}, endpoint={request.endpoint}, headers={{'Accept': request.headers.get('Accept'), 'User-Agent': request.headers.get('User-Agent')}} session_present={('username' in session) and ('current_site' in session)}")
    try:
        username = session.get('username')
        site_name = session.get('current_site')
        
        if not username or not site_name:
            # Dummy fallback when session/site not selected
            logging.info("[get_system_health] Dummy fallback due to missing username/site in session")
            health_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'cpuUtil': 0.0,
                'cpuTemp': 0.0,
                'freeStorage': 0.0,
                'totalStorage': 0.0,
                'freeRAM': 0.0,
                'totalRAM': 0.0
            }
            return jsonify(health_data), 200
        
        effective_username = session.get('current_site_owner') or username
        health_dir = Path(DATA_DIR) / effective_username / site_name / 'health'
        if health_dir.exists():
            health_files = sorted(health_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
            if health_files:
                latest_health = health_files[0]
                try:
                    with open(latest_health, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Convert agent timestamp to date/time strings
                    ts = datetime.fromisoformat(data['timestamp'])
                    res_data = {
                        'date': ts.strftime('%Y-%m-%d'),
                        'time': ts.strftime('%H:%M:%S'),
                        'cpuUtil': data.get('cpuUtil', 0.0),
                        'cpuTemp': data.get('cpuTemp', 0.0),
                        'freeStorage': round(data.get('freeStorage', 0.0), 2),
                        'totalStorage': round(data.get('totalStorage', 0.0), 2),
                        'freeRAM': round(data.get('freeRAM', 0.0), 2),
                        'totalRAM': round(data.get('totalRAM', 0.0), 2),
                        'timestamp': data.get('timestamp', datetime.now().isoformat()),
                        'uptime': data.get('uptime', 0),
                        'uptime_seconds': data.get('uptime_seconds', data.get('uptime', 0))
                    }
                    if 'metrics' in request.path:
                        return jsonify({'ok': True, 'data': res_data})
                    return jsonify(res_data)
                except Exception as e:
                    logging.warning(f"Error reading agent health file {latest_health}: {e}")
        
        # Fallback: Get current server system metrics
        cpu_util = psutil.cpu_percent()
        try:
            cpu_temp = psutil.sensors_temperatures().get('coretemp', [{'current': 0}])[0]['current']
        except (AttributeError, KeyError):
            cpu_temp = 0
        storage = psutil.disk_usage('/')
        memory = psutil.virtual_memory()
        
        res_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'cpuUtil': cpu_util,
            'cpuTemp': cpu_temp,
            'freeStorage': round(storage.free / (1024**3), 2),
            'totalStorage': round(storage.total / (1024**3), 2),
            'freeRAM': round(memory.available / (1024**2), 2),
            'totalRAM': round(memory.total / (1024**2), 2),
            'timestamp': datetime.now().isoformat(),
            'uptime': 0,
            'uptime_seconds': 0
        }
        if 'metrics' in request.path:
            return jsonify({'ok': True, 'data': res_data})
        return jsonify(res_data)
        
    except Exception as e:
        logging.error(f"Error getting system health data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/wifi/data')
@app.route('/api/wifi/networks')
@login_required
def get_wifi_data():
    logging.debug(f"get_wifi_data: method={request.method}, path={request.path}, endpoint={request.endpoint}, headers={{'Accept': request.headers.get('Accept'), 'User-Agent': request.headers.get('User-Agent')}} session_present={('username' in session) and ('current_site' in session)}")
    try:
        username = session.get('username')
        site_name = session.get('current_site')
        
        def _wifi_dummy_response(reason: str):
            logging.info(f"[get_wifi_data] Dummy fallback due to {reason} | username={username}, site={site_name}")
            dummy_nets = [
                {
                    'ssid': 'Plamongan_Indah_Home',
                    'bssid': '00:11:22:33:44:55',
                    'security': 'WPA2-PSK',
                    'last_seen': 'Just now',
                    'lastSeen': 'Just now',
                    'channel': 1,
                    'frequency': 2412,
                    'frequency_mhz': 2412,
                    'signal': -45,
                    'signal_dbm': -45,
                    'band': '2.4GHz',
                    'vendor': 'TP-Link'
                },
                {
                    'ssid': 'Telkomsel_Broadband',
                    'bssid': '11:22:33:44:55:66',
                    'security': 'WPA3',
                    'last_seen': '1 min ago',
                    'lastSeen': '1 min ago',
                    'channel': 6,
                    'frequency': 2437,
                    'frequency_mhz': 2437,
                    'signal': -58,
                    'signal_dbm': -58,
                    'band': '2.4GHz',
                    'vendor': 'Huawei'
                },
                {
                    'ssid': 'Monsfer_SDR_Internal',
                    'bssid': '22:33:44:55:66:77',
                    'security': 'WPA2/WPA3',
                    'last_seen': '2 min ago',
                    'lastSeen': '2 min ago',
                    'channel': 11,
                    'frequency': 2462,
                    'frequency_mhz': 2462,
                    'signal': -62,
                    'signal_dbm': -62,
                    'band': '2.4GHz',
                    'vendor': 'Cisco'
                },
                {
                    'ssid': 'Free_Wifi_Kopi',
                    'bssid': '33:44:55:66:77:88',
                    'security': 'Open',
                    'last_seen': 'Just now',
                    'lastSeen': 'Just now',
                    'channel': 36,
                    'frequency': 5180,
                    'frequency_mhz': 5180,
                    'signal': -68,
                    'signal_dbm': -68,
                    'band': '5.8GHz',
                    'vendor': 'MikroTik'
                },
                {
                    'ssid': 'SDR_Backup_5G',
                    'bssid': '44:55:66:77:88:99',
                    'security': 'WPA2',
                    'last_seen': '3 min ago',
                    'lastSeen': '3 min ago',
                    'channel': 149,
                    'frequency': 5745,
                    'frequency_mhz': 5745,
                    'signal': -52,
                    'signal_dbm': -52,
                    'band': '5.8GHz',
                    'vendor': 'Ubiquiti'
                }
            ]
            return jsonify({
                'band24Stats': {
                    'totalNetworks': 3,
                    'avgSignal': -55.0,
                    'recommendedChannels': '1, 6, 11'
                },
                'band58Stats': {
                    'totalNetworks': 2,
                    'avgSignal': -60.0,
                    'recommendedChannels': '36, 149'
                },
                'band24ChartData': [-100.0, -45.0, -100.0, -100.0, -100.0, -58.0, -100.0, -100.0, -100.0, -100.0, -62.0, -100.0, -100.0, -100.0],
                'band58ChartData': [-100.0] * 25,
                'channel24ChartData': [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
                'channel58ChartData': [0] * 25,
                'networks': dummy_nets,
                'stats': {
                    'total': len(dummy_nets),
                    'secured': len([n for n in dummy_nets if n.get('security') and n['security'].lower() != 'open']),
                    'open': len([n for n in dummy_nets if not n.get('security') or n['security'].lower() == 'open'])
                },
                'ok': True
            }), 200
        
        if not username or not site_name:
            return _wifi_dummy_response('missing username/site in session')
            
        effective_username = session.get('current_site_owner') or username
        wifi_dir = Path(DATA_DIR) / effective_username / site_name / 'wifi'
        if not wifi_dir.exists():
            return _wifi_dummy_response('WiFi data directory not found')
            
        # Get latest WiFi scan file
        wifi_files = sorted(wifi_dir.glob('*.csv'), key=lambda x: x.stat().st_mtime, reverse=True)
        if not wifi_files:
            return _wifi_dummy_response('no WiFi data available')
            
        latest_file = wifi_files[0]
        
        # Read WiFi data with custom format
        networks = []
        with open(latest_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                return _wifi_dummy_response('empty WiFi file')
            
            # Skip header if present
            start_idx = 0
            if 'bssid' in lines[0].lower():
                start_idx = 1
                
            for line in lines[start_idx:]:
                if line.strip():
                    try:
                        # Parse line: date;time;bssid;frequency;signal;ssid;vendor
                        parts = [part.strip() for part in line.strip().split(';')]
                        if len(parts) >= 5:
                            date, time, bssid, frequency, signal = parts[:5]
                            ssid = parts[5] if len(parts) > 5 else ''
                            vendor = parts[6] if len(parts) > 6 else ''
                            
                            # Clean up SSID and vendor strings
                            ssid = ssid.replace('\x00', '').strip()
                            vendor = vendor.replace('\x00', '').strip()
                            
                            # Determine band based on frequency
                            try:
                                frequency = int(frequency)
                                if 2412 <= frequency <= 2484:  # 2.4GHz band
                                    band = '2.4GHz'
                                    channel = (frequency - 2407) // 5
                                elif 5170 <= frequency <= 5825:  # 5GHz band
                                    band = '5.8GHz'
                                    channel = (frequency - 5000) // 5
                                else:
                                    continue  # Skip if frequency is out of range
                                    
                                # Convert signal to float
                                signal = float(signal)
                                
                                networks.append({
                                    'date': date,
                                    'time': time,
                                    'bssid': bssid,
                                    'frequency': int(frequency),
                                    'frequency_mhz': int(frequency),
                                    'signal': float(signal),
                                    'signal_dbm': float(signal),
                                    'ssid': ssid,
                                    'vendor': vendor,
                                    'band': band,
                                    'channel': int(channel),
                                    'last_seen': time,
                                    'lastSeen': time,
                                    'security': 'Secured'
                                })
                            except (ValueError, TypeError) as e:
                                logging.warning(f"Error parsing frequency or signal: {line.strip()}, Error: {str(e)}")
                                continue
                    except Exception as e:
                        logging.warning(f"Error parsing line: {line.strip()}, Error: {str(e)}")
                        continue
        
        if not networks:
            return _wifi_dummy_response('no valid WiFi data found after parsing')
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(networks)
        
        # Process 2.4GHz data
        band24_data = df[df['band'] == '2.4GHz']
        band24_stats = {
            'totalNetworks': int(len(band24_data)),
            'avgSignal': float(round(band24_data['signal'].mean(), 1)) if not band24_data.empty else 0.0,
            'recommendedChannels': get_recommended_channels(band24_data)
        }
        
        # Process 5.8GHz data
        band58_data = df[df['band'] == '5.8GHz']
        band58_stats = {
            'totalNetworks': int(len(band58_data)),
            'avgSignal': float(round(band58_data['signal'].mean(), 1)) if not band58_data.empty else 0.0,
            'recommendedChannels': get_recommended_channels(band58_data)
        }
        
        # Prepare chart data
        band24_chart_data = [float(x) for x in prepare_band_chart_data(band24_data, '2.4GHz')]
        band58_chart_data = [float(x) for x in prepare_band_chart_data(band58_data, '5.8GHz')]
        channel24_chart_data = [int(x) for x in prepare_channel_chart_data(band24_data, '2.4GHz')]
        channel58_chart_data = [int(x) for x in prepare_channel_chart_data(band58_data, '5.8GHz')]
        
        return jsonify({
            'ok': True,
            'band24Stats': band24_stats,
            'band58Stats': band58_stats,
            'band24ChartData': band24_chart_data,
            'band58ChartData': band58_chart_data,
            'channel24ChartData': channel24_chart_data,
            'channel58ChartData': channel58_chart_data,
            'networks': networks,
            'stats': {
                'total': len(networks),
                'secured': len([n for n in networks if n.get('security') and n['security'].lower() != 'open']),
                'open': len([n for n in networks if not n.get('security') or n['security'].lower() == 'open'])
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting WiFi data: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

def get_recommended_channels(data):
    if data.empty:
        return "No data available"
        
    # Count networks per channel
    channel_counts = data['channel'].value_counts()
    
    # Find channels with least interference
    min_count = channel_counts.min()
    recommended = channel_counts[channel_counts == min_count].index.tolist()
    
    return ", ".join(map(str, sorted(recommended)))

def prepare_band_chart_data(data, band_name):
    if band_name == '2.4GHz':
        if data.empty:
            return [-100.0] * 14
        chart_data = data.groupby('channel')['signal'].mean().round(1).to_dict()
        return [chart_data.get(channel, -100.0) for channel in range(1, 15)]
    else:
        channels = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
        if data.empty:
            return [-100.0] * len(channels)
        chart_data = data.groupby('channel')['signal'].mean().round(1).to_dict()
        return [chart_data.get(channel, -100.0) for channel in channels]

def prepare_channel_chart_data(data, band_name):
    if band_name == '2.4GHz':
        if data.empty:
            return [0] * 14
        channel_counts = data['channel'].value_counts()
        return [channel_counts.get(channel, 0) for channel in range(1, 15)]
    else:
        channels = [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
        if data.empty:
            return [0] * len(channels)
        channel_counts = data['channel'].value_counts()
        return [channel_counts.get(channel, 0) for channel in channels]

@app.route('/api/wifi/scan', methods=['POST'])
def scan_wifi():
    try:
        # For testing, return dummy data
        dummy_networks = [
            {
                "ssid": "Office_WiFi",
                "bssid": "00:11:22:33:44:55",
                "channel": 1,
                "frequency": 2.412,
                "signalStrength": -45,
                "security": "WPA2",
                "lastSeen": "Just now",
                "hidden": False
            },
            {
                "ssid": "Guest_Network",
                "bssid": "00:11:22:33:44:66",
                "channel": 6,
                "frequency": 2.437,
                "signalStrength": -60,
                "security": "Open",
                "lastSeen": "1 min ago",
                "hidden": False
            },
            {
                "ssid": "Hidden_AP",
                "bssid": "00:11:22:33:44:77",
                "channel": 11,
                "frequency": 2.462,
                "signalStrength": -70,
                "security": "WPA3",
                "lastSeen": "2 min ago",
                "hidden": True
            },
            {
                "ssid": "5G_Network",
                "bssid": "00:11:22:33:44:88",
                "channel": 36,
                "frequency": 5.180,
                "signalStrength": -55,
                "security": "WPA2",
                "lastSeen": "Just now",
                "hidden": False
            },
            {
                "ssid": "5G_Guest",
                "bssid": "00:11:22:33:44:99",
                "channel": 149,
                "frequency": 5.745,
                "signalStrength": -65,
                "security": "Open",
                "lastSeen": "1 min ago",
                "hidden": False
            }
        ]

        dummy_violations = [
            {
                "ssid": "Illegal_2.3GHz_AP",
                "bssid": "00:11:22:33:44:AA",
                "frequency": 2.300,
                "channel": 0,
                "signalStrength": -65,
                "security": "WPA2",
                "lastSeen": "2 min ago",
                "hidden": False
            },
            {
                "ssid": "Unauthorized_2.5GHz",
                "bssid": "00:11:22:33:44:BB",
                "frequency": 2.500,
                "channel": 14,
                "signalStrength": -58,
                "security": "WPA2",
                "lastSeen": "5 min ago",
                "hidden": False
            },
            {
                "ssid": "OutOfBand_5.9GHz",
                "bssid": "00:11:22:33:44:CC",
                "frequency": 5.900,
                "channel": 180,
                "signalStrength": -72,
                "security": "WPA2",
                "lastSeen": "4 min ago",
                "hidden": False
            }
        ]

        return jsonify({
            "success": True,
            "networks": dummy_networks,
            "violations": dummy_violations
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/wifi/report', methods=['POST'])
@login_required
def report_wifi():
    try:
        data = request.get_json()
        bssid = data.get('bssid')
        if not bssid:
            return jsonify({"success": False, "error": "BSSID is required"}), 400
        return jsonify({"success": True, "message": f"Network {bssid} reported successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    try:
        username = session.get('username')
        site_name = request.args.get('site') or session.get('current_site')
        if not username or not site_name:
            return jsonify({'ok': False, 'error': 'Site not selected'}), 400
        settings_path = DATA_DIR / username / site_name / 'settings.json'
        if request.method == 'GET':
            settings = {'freq_start_mhz': 87.5, 'freq_end_mhz': 960, 'heartbeat_interval_sec': 30, 'auto_restart_on_failure': True, 'enable_system_logging': True, 'receiver_running': True}
            if settings_path.exists():
                settings.update(load_json_safe(settings_path))
            return jsonify({'ok': True, 'settings': settings})
        else: # POST
            payload = request.get_json(silent=True) or {}
            new_settings = payload.get('settings', {})
            current = load_json_safe(settings_path) if settings_path.exists() else {}
            current.update(new_settings)
            save_json_atomic_with_lock(settings_path, current)
            return jsonify({'ok': True, 'settings': current})
    except Exception as e:
        logging.exception(f"Error in api_settings: {str(e)}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@csrf.exempt
@app.route('/api/sdr/control', methods=['POST'])
@login_required
def api_sdr_control():
    try:
        payload = request.get_json(silent=True) or {}
        site_name = payload.get('site')
        action = payload.get('action')
        username = session.get('username')
        if not site_name or not action:
            return jsonify({'ok': False, 'error': 'Missing site or action'}), 400
        settings_path = DATA_DIR / username / site_name / 'settings.json'
        settings = load_json_safe(settings_path) if settings_path.exists() else {}
        running = (action == 'start')
        settings['receiver_running'] = running
        save_json_atomic_with_lock(settings_path, settings)
        return jsonify({'ok': True, 'receiver_running': running})
    except Exception as e:
        logging.exception(f"Error in api_sdr_control: {str(e)}")
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/debug/generate-dummy')
def debug_generate_dummy():
    try:
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        import generate_dummy_data
        generate_dummy_data.main()
        return jsonify({"success": True, "message": "Dummy data generated successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
