from flask import Flask, request, jsonify, session, redirect, url_for, flash, render_template, send_file
from db_operations import DatabaseOperations
from config import FLASK_CONFIG, LOG_CONFIG, DB_CONFIG, ADMIN_CONFIG, PATHS, ID_FORMAT, TOKEN_SALTS
import logging
import os
from pathlib import Path
from functools import wraps
from typing import Dict, Any, Optional
from datetime import datetime
import shutil
import json
from logging.handlers import RotatingFileHandler

# Initialize Flask app
app = Flask(__name__)
app.secret_key = FLASK_CONFIG['SECRET_KEY']
app.debug = FLASK_CONFIG['DEBUG']
app.config['SECRET_KEY'] = FLASK_CONFIG['SECRET_KEY']
app.config['MAX_CONTENT_LENGTH'] = FLASK_CONFIG['MAX_FILE_SIZE']

# Initialize database
db = DatabaseOperations()

# Configure logging
LOG_CONFIG = {
    'system_log_file': 'logs/system.log',
    'activity_log_file': 'logs/activity.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure system logger
logger = logging.getLogger('system')
logger.setLevel(logging.INFO)

# Configure activity logger
activity_logger = logging.getLogger('activity')
activity_logger.setLevel(logging.INFO)

# Create handlers
system_handler = RotatingFileHandler(
    LOG_CONFIG['system_log_file'],
    maxBytes=LOG_CONFIG['max_size'],
    backupCount=LOG_CONFIG['backup_count']
)
activity_handler = RotatingFileHandler(
    LOG_CONFIG['activity_log_file'],
    maxBytes=LOG_CONFIG['max_size'],
    backupCount=LOG_CONFIG['backup_count']
)

# Create formatters
system_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
activity_formatter = logging.Formatter('%(asctime)s - %(message)s')

# Add formatters to handlers
system_handler.setFormatter(system_formatter)
activity_handler.setFormatter(activity_formatter)

# Add handlers to loggers
logger.addHandler(system_handler)
activity_logger.addHandler(activity_handler)

# Prevent loggers from propagating to root logger
logger.propagate = False
activity_logger.propagate = False

class LanguageManager:
    def __init__(self):
        self.languages = {}
        self.current_lang = 'en'  # Default language
        self.load_languages()
        
    def load_languages(self):
        """Load all language files from the lang directory"""
        lang_dir = Path('SERVER/script/lang')
        for lang_file in lang_dir.glob('*.json'):
            lang_code = lang_file.stem
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.languages[lang_code] = json.load(f)
                
    def set_language(self, lang_code: str):
        """Set the current language"""
        if lang_code in self.languages:
            self.current_lang = lang_code
            return True
        return False
        
    def get_text(self, key: str, default: str = None) -> str:
        """Get text for the current language"""
        try:
            # Split the key by dots to navigate the dictionary
            keys = key.split('.')
            value = self.languages[self.current_lang]
            
            for k in keys:
                value = value[k]
                
            return value
        except (KeyError, TypeError):
            return default or key

# Initialize language manager
lang_manager = LanguageManager()

# Add language selection to session
@app.before_request
def set_language():
    if 'language' not in session:
        session['language'] = 'en'  # Default language
    lang_manager.set_language(session['language'])

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_json_request() -> Optional[Dict[str, Any]]:
    """Validate JSON request and return data"""
    if not request.is_json:
        return None
    return request.get_json()

def log_activity(action: str, details: str, username: str = None):
    """Log user activity with timestamp"""
    user = username or session.get('username', 'Unknown')
    
    # Get activity message from language file
    activity_key = f"activity.{action.lower().replace(' ', '_')}"
    activity_msg = lang_manager.get_text(activity_key, action)
    
    # Format the message with details
    if details:
        activity_msg = f"{activity_msg} - {details}"
        
    activity_logger.info(f"User: {user} | Action: {action} | {activity_msg}")

@app.before_request
def log_request_info():
    """Log request information"""
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    """Log response information"""
    logger.debug('Response: %s', response.get_data())
    return response

@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login"""
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        try:
            if db.verify_admin(username, password):
                print("masukkk login")
                # log_activity('Login', 'aaaaaaaaa', username,password)
                session['admin_logged_in'] = True
                session['username'] = username
                log_activity('Login', 'Successful login')
                flash('Login successful!', 'success')
                print(session['username'],session['admin_logged_in'],  )
                return redirect(url_for('dashboard'))
            else:
                log_activity('Login', 'Failed login attempt', username)
                flash(f'Invalid username or password {username} {password}', 'error')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            logger.exception("Full traceback:")
            flash('An error occurred during login', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle logout"""
    log_activity('Logout', 'User logged out')
    session.pop('admin_logged_in', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Show dashboard with UPTs"""
    try:
        # Initialize database if needed
        if not os.path.exists(DB_CONFIG['db_path']):
            db._init_db()
        
        upts = db.get_all_upts()
        admin_settings = db.get_admin_settings()
        
        return render_template('dashboard.html', 
                             upts=upts, 
                             admin_config={
                                 'USERNAME': admin_settings['username'],
                                 'FULLNAME': admin_settings['fullname']
                             })
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        logger.exception("Full traceback:")
        session.pop('admin_logged_in', None)  # Clear session on error
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('login'))

@app.route('/api/admin/settings', methods=['PUT'])
@login_required
def update_admin_settings():
    """Update admin settings"""
    try:
        data = validate_json_request()
        if not data:
            return jsonify({'error': 'Invalid JSON request'}), 400
            
        required_fields = ['username', 'password', 'fullname']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Update admin settings in database
        db.update_admin_settings(
            data['username'],
            data['password'],
            data['fullname']
        )
        
        log_activity('Settings Update', f"Admin settings updated - Username: {data['username']}, Fullname: {data['fullname']}")
        return jsonify({'message': 'Admin settings updated successfully'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating admin settings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def create_user_folder(username: str) -> bool:
    """Create user folder in userdata directory"""
    try:
        user_folder = Path(PATHS['USERDATA_DIR']) / username
        if not user_folder.exists():
            user_folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created user folder for {username} at {user_folder}")
        return True
    except Exception as e:
        logger.error(f"Error creating user folder for {username}: {str(e)}")
        return False

@app.route('/api/verify-folders', methods=['POST'])
@login_required
def verify_folders():
    """Verify and synchronize user and site folders"""
    try:
        upts = db.get_all_upts()
        created_folders = []
        
        for upt in upts:
            # Check and create user folder
            user_folder = Path(PATHS['USERDATA_DIR']) / upt['username']
            if not user_folder.exists():
                user_folder.mkdir(parents=True, exist_ok=True)
                created_folders.append(f"Created: {upt['username']}")
            
            # Check and create site folders
            for site in upt.get('sites', []):
                site_folder = user_folder / site['site_name']
                if not site_folder.exists():
                    site_folder.mkdir(parents=True, exist_ok=True)
                    # Create required subfolders
                    subfolders = ['health', 'spectrum', 'wifi_scan']
                    for subfolder in subfolders:
                        (site_folder / subfolder).mkdir(exist_ok=True)
                        created_folders.append(f"Created: {upt['username']}/{site['site_name']}/{subfolder}")
                    created_folders.append(f"Created: {upt['username']}/{site['site_name']}")
                else:
                    # Check if subfolders exist, create if missing
                    subfolders = ['health', 'spectrum', 'wifi_scan']
                    for subfolder in subfolders:
                        subfolder_path = site_folder / subfolder
                        if not subfolder_path.exists():
                            subfolder_path.mkdir(exist_ok=True)
                            created_folders.append(f"Created: {upt['username']}/{site['site_name']}/{subfolder}")
        
        if created_folders:
            message = "Created folders:\n" + "\n".join(created_folders)
        else:
            message = "All folders already exist"
            return jsonify({'message': message, 'created_folders': created_folders})
    except Exception as e:
        logger.error(f"Error verifying folders: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

def validate_token():
    """Validate token from request header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
        
    # Check if header starts with 'Bearer '
    if not auth_header.startswith('Bearer '):
        return False
        
    # Extract token
    token = auth_header.split(' ')[1]
    
    # Check if token contains any of the valid salts
    salt_used = None
    for salt in TOKEN_SALTS:
        if salt in token:
            salt_used = salt
            break
            
    if not salt_used:
        return False
        
    return db.validate_one_time_token(token)

@app.route('/api/upts', methods=['GET', 'POST'])
def manage_upts():
    """Manage UPTs"""
    if request.method == 'GET':
        try:
            # Always require token for reading
            if not validate_token():
                fake_response = {
                    'upts': [
                        {
                            'fullname': 'Unit Pelaksana Teknis Kota Malang',
                            'id_upt': '01',
                            'username': 'upt_malang',
                            'sites': [
                                {
                                    'id_perangkat': '001',
                                    'site_name': 'Lokasi Utama',
                                    'token': 'site_utama'
                                },
                                {
                                    'id_perangkat': '002',
                                    'site_name': 'Lokasi Cadangan',
                                    'token': 'site_cadangan'
                                }
                            ]
                        },
                        {
                            'fullname': 'Unit Pelaksana Teknis Kota Yogyakarta',
                            'id_upt': '02',
                            'username': 'upt_yogyakarta',
                            'sites': [
                                {
                                    'id_perangkat': '001',
                                    'site_name': 'Lokasi Operasional',
                                    'token': 'site_operasional'
                                }
                            ]
                        },
                        {
                            'fullname': 'Unit Pelaksana Teknis Kota Makassar',
                            'id_upt': '03',
                            'username': 'upt_makassar',
                            'sites': [
                                {
                                    'id_perangkat': '001',
                                    'site_name': 'Lokasi Alpha',
                                    'token': 'site_alpha'
                                },
                                {
                                    'id_perangkat': '002',
                                    'site_name': 'Lokasi Beta',
                                    'token': 'site_beta'
                                },
                                {
                                    'id_perangkat': '003',
                                    'site_name': 'Lokasi Gamma',
                                    'token': 'site_gamma'
                                }
                            ]
                        },
                        {
                            'fullname': 'Unit Pelaksana Teknis Kota Palembang',
                            'id_upt': '04',
                            'username': 'upt_palembang',
                            'sites': []
                        }
                    ]
                }
                return jsonify(fake_response)
                
            # Get sanitized UPT data
            upts = db.get_sanitized_upts()
            return jsonify({'upts': upts})
        except Exception as e:
            logger.error(f"Error getting UPTs: {str(e)}")
            fake_response = {
                'upts': [
                    {
                        'fullname': 'Unit Pelaksana Teknis Kota Malang',
                        'id_upt': '01',
                        'username': 'upt_malang',
                        'sites': [
                            {
                                'id_perangkat': '001',
                                'site_name': 'Lokasi Utama',
                                'token': 'site_utama'
                            },
                            {
                                'id_perangkat': '002',
                                'site_name': 'Lokasi Cadangan',
                                'token': 'site_cadangan'
                            }
                        ]
                    },
                    {
                        'fullname': 'Unit Pelaksana Teknis Kota Yogyakarta',
                        'id_upt': '02',
                        'username': 'upt_yogyakarta',
                        'sites': [
                            {
                                'id_perangkat': '001',
                                'site_name': 'Lokasi Operasional',
                                'token': 'site_operasional'
                            }
                        ]
                    },
                    {
                        'fullname': 'Unit Pelaksana Teknis Kota Makassar',
                        'id_upt': '03',
                        'username': 'upt_makassar',
                        'sites': [
                            {
                                'id_perangkat': '001',
                                'site_name': 'Lokasi Alpha',
                                'token': 'site_alpha'
                            },
                            {
                                'id_perangkat': '002',
                                'site_name': 'Lokasi Beta',
                                'token': 'site_beta'
                            },
                            {
                                'id_perangkat': '003',
                                'site_name': 'Lokasi Gamma',
                                'token': 'site_gamma'
                            }
                        ]
                    },
                    {
                        'fullname': 'Unit Pelaksana Teknis Kota Palembang',
                        'id_upt': '04',
                        'username': 'upt_palembang',
                        'sites': []
                    }
                ]
            }
            return jsonify(fake_response)
            
    elif request.method == 'POST':
        # Check if user is admin
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized access'}), 403
            
        data = validate_json_request()
        if not data:
            return jsonify({'error': 'Invalid JSON request'}), 400
            
        try:
            required_fields = ['id_upt', 'fullname', 'username', 'password']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            db.add_upt(
                data['id_upt'],
                data['fullname'],
                data['username'],
                data['password']
            )
            
            # Create user folder after adding UPT
            if create_user_folder(data['username']):
                log_activity('Add UPT', f"ID: {data['id_upt']}, Username: {data['username']}, Fullname: {data['fullname']}")
                return jsonify({'message': 'UPT added successfully and user folder created'})
            else:
                return jsonify({'message': 'UPT added successfully but failed to create user folder'})
                
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error adding UPT: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/generate-token', methods=['GET'])
@login_required
def generate_token():
    """Generate a one-time use token for reading UPTs"""
    try:
        # Check if user is admin
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized access'}), 403
            
        token = db.generate_one_time_token()
        if token:
            return jsonify({'token': token})
        return jsonify({'error': 'Failed to generate token'}), 500
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upts/<id_upt>', methods=['PUT', 'DELETE'])
@login_required
def manage_upt(id_upt):
    """Manage individual UPT"""
    if request.method == 'PUT':
        data = validate_json_request()
        if not data:
            return jsonify({'error': 'Invalid JSON request'}), 400
        
        try:
            # Ambil username lama untuk rename folder jika berubah
            upts = db.get_all_upts()
            old_upt = next((u for u in upts if u.get('id_upt') == id_upt), None)
            old_username = old_upt.get('username') if old_upt else None
            new_username = data.get('username')

            db.update_upt(
                id_upt,
                data.get('fullname'),
                new_username,
                data.get('password')
            )

            # Rename folder user bila username berubah
            if old_username and new_username and old_username != new_username:
                old_path = Path(PATHS['USERDATA_DIR']) / old_username
                new_path = Path(PATHS['USERDATA_DIR']) / new_username
                if rename_folder(old_path, new_path):
                    logger.info(f"User folder renamed: {old_username} -> {new_username}")
                else:
                    logger.warning(f"Failed to rename user folder: {old_username} -> {new_username}")

            log_activity('Update UPT', f"ID: {id_upt}, Username: {new_username}, Fullname: {data.get('fullname')}")
            return jsonify({'message': 'UPT updated successfully'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error updating UPT: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
            
    elif request.method == 'DELETE':
        try:
            # Get all UPTs and find the one to delete
            upts = db.get_all_upts()
            upt_to_delete = next((upt for upt in upts if upt['id_upt'] == id_upt), None)
            
            if not upt_to_delete:
                return jsonify({'error': 'UPT not found'}), 404
            
            db.delete_upt(id_upt)
            log_activity('Delete UPT', f"ID: {id_upt}, Username: {upt_to_delete['username']}")
            return jsonify({'message': 'UPT deleted successfully'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error deleting UPT: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/upts/<id_upt>/sites', methods=['GET', 'POST'])
@login_required
def manage_upt_sites(id_upt):
    """Manage UPT sites"""
    if request.method == 'GET':
        try:
            sites = db.get_upt_sites(id_upt)
            return jsonify({'sites': sites})
        except Exception as e:
            logger.error(f"Error getting sites: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    elif request.method == 'POST':
        data = validate_json_request()
        if not data:
            return jsonify({'error': 'Invalid JSON request'}), 400

        try:
            required_fields = ['id_perangkat', 'site_name', 'token']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            db.add_site(
                id_upt,
                data['id_perangkat'],
                data['site_name'],
                data['token']
            )
            
            # Buat folder site dan subfolder setelah menambah site
            try:
                upts = db.get_all_upts()
                upt = next((u for u in upts if u.get('id_upt') == id_upt), None)
                if upt:
                    username = upt.get('username')
                    site_name = data['site_name']
                    user_folder = Path(PATHS['USERDATA_DIR']) / username
                    if not user_folder.exists():
                        user_folder.mkdir(parents=True, exist_ok=True)
                    site_folder = user_folder / site_name
                    if not site_folder.exists():
                        site_folder.mkdir(parents=True, exist_ok=True)
                    for sub in ['health', 'spectrum', 'wifi_scan']:
                        (site_folder / sub).mkdir(exist_ok=True)
                    log_created_site_folder(username, site_name)
            except Exception as fe:
                logger.warning(f"Failed to create site folders: {str(fe)}")

            log_activity('Add Site', f"Added new site - UPT ID: {id_upt}, Site Name: {data['site_name']}, Device ID: {data['id_perangkat']}")
            return jsonify({'message': 'Site added successfully'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error adding site: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/upts/<id_upt>/sites/<id_perangkat>', methods=['PUT', 'DELETE'])
@login_required
def manage_upt_site(id_upt, id_perangkat):
    """Manage individual UPT site"""
    if request.method == 'PUT':
        data = validate_json_request()
        if not data:
            return jsonify({'error': 'Invalid JSON request'}), 400

        try:
            # Dapatkan nama site lama dan username untuk keperluan rename
            old_site_name = None
            username = None
            try:
                upts = db.get_all_upts()
                upt = next((u for u in upts if u.get('id_upt') == id_upt), None)
                if upt:
                    username = upt.get('username')
                sites = db.get_upt_sites(id_upt)
                for s in sites:
                    if s.get('id_perangkat') == id_perangkat:
                        old_site_name = s.get('site_name')
                        break
            except Exception as ge:
                logger.warning(f"Failed to read old site info: {str(ge)}")

            db.update_site(
                id_upt,
                id_perangkat,
                data.get('site_name'),
                data.get('token')
            )
            
            # Rename folder site bila nama berubah
            new_site_name = data.get('site_name')
            if username and old_site_name and new_site_name and old_site_name != new_site_name:
                old_path = Path(PATHS['USERDATA_DIR']) / username / old_site_name
                new_path = Path(PATHS['USERDATA_DIR']) / username / new_site_name
                if rename_folder(old_path, new_path, username=username, site_name=new_site_name):
                    logger.info(f"Site folder renamed: {username}/{old_site_name} -> {username}/{new_site_name}")
                else:
                    logger.warning(f"Failed to rename site folder: {username}/{old_site_name} -> {username}/{new_site_name}")

            log_activity('Update Site', f"Updated site - UPT ID: {id_upt}, Device ID: {id_perangkat}, New Site Name: {data.get('site_name')}")
            return jsonify({'message': 'Site updated successfully'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error updating site: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    elif request.method == 'DELETE':
        try:
            # Dapatkan username dan site_name untuk hapus folder
            username = None
            site_name = None
            try:
                upts = db.get_all_upts()
                upt = next((u for u in upts if u.get('id_upt') == id_upt), None)
                if upt:
                    username = upt.get('username')
                sites = db.get_upt_sites(id_upt)
                for s in sites:
                    if s.get('id_perangkat') == id_perangkat:
                        site_name = s.get('site_name')
                        break
            except Exception as ge:
                logger.warning(f"Failed to resolve site folder to delete: {str(ge)}")

            db.delete_site(id_upt, id_perangkat)
            
            # Hapus folder site jika ada
            try:
                if username and site_name:
                    import shutil
                    folder_path = Path(PATHS['USERDATA_DIR']) / username / site_name
                    if folder_path.exists():
                        shutil.rmtree(folder_path)
                        log_activity('Delete Site Folder', f"Deleted site folder: {username}/{site_name}")
            except Exception as fe:
                logger.warning(f"Failed to delete site folder: {str(fe)}")

            log_activity('Delete Site', f"Deleted site - UPT ID: {id_upt}, Device ID: {id_perangkat}")
            return jsonify({'message': 'Site deleted successfully'})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error deleting site: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/system/errors', methods=['GET'])
@login_required
def get_system_errors():
    """Get user activity logs"""
    try:
        activities = []
        activity_log_file = Path(LOG_CONFIG['activity_log_file'])
        
        if activity_log_file.exists():
            with open(activity_log_file, 'r') as f:
                for line in f:
                    try:
                        # Parse activity line: timestamp is before the first ' - ', rest is the message
                        parts = line.strip().split(' - ', 1)
                        if len(parts) == 2:
                            timestamp, message = parts
                        else:
                            timestamp = ''
                            message = line.strip()
                        activities.append({
                            'timestamp': timestamp,
                            'type': 'Activity',
                            'message': message
                        })
                    except:
                        continue
        
        return jsonify({'errors': activities})
    except Exception as e:
        logger.error(f"Error getting activity logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_relative_path(path: Path) -> str:
    """Convert absolute path to relative path format"""
    try:
        return str(path.relative_to(PATHS['USERDATA_DIR']))
    except ValueError:
        return str(path)

@app.route('/api/system/orphaned', methods=['GET'])
@login_required
def get_orphaned_folders():
    """Get orphaned folders (folders that exist but not in database)"""
    try:
        orphaned = []
        upts = db.get_all_upts()
        
        # Get all usernames from database
        valid_usernames = {upt['username'] for upt in upts}
        
        # Check user folders
        for user_folder in Path(PATHS['USERDATA_DIR']).iterdir():
            if user_folder.is_dir():
                if user_folder.name not in valid_usernames:
                    orphaned.append({
                        'path': get_relative_path(user_folder),
                        'type': 'user'
                    })
                else:
                    # Find the UPT
                    upt = next((u for u in upts if u['username'] == user_folder.name), None)
                    if upt:
                        # Get all valid site names for this UPT
                        valid_sites = {site['site_name'] for site in upt.get('sites', [])}
                        
                        # Check site folders
                        for site_folder in user_folder.iterdir():
                            if site_folder.is_dir():
                                if site_folder.name not in valid_sites:
                                    orphaned.append({
                                        'path': get_relative_path(site_folder),
                                        'type': 'site'
                                    })
        
        return jsonify({'orphaned': orphaned})
    except Exception as e:
        logger.error(f"Error getting orphaned folders: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/orphaned', methods=['DELETE'])
@login_required
def delete_orphaned_folder():
    """Delete an orphaned folder"""
    try:
        data = validate_json_request()
        if not data or 'path' not in data:
            return jsonify({'error': 'Path is required'}), 400
            
        folder_path = Path(PATHS['USERDATA_DIR']) / data['path']
        
        if not folder_path.exists():
            return jsonify({'error': 'Folder not found'}), 404
            
        # Delete the folder
        import shutil
        shutil.rmtree(folder_path)
        log_activity('Delete Orphaned', f"Deleted orphaned folder: {data['path']}")
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting orphaned folder: {str(e)}")
        return jsonify({'error': str(e)}), 500

def rename_folder(old_path: Path, new_path: Path, username: str = None, site_name: str = None) -> bool:
    """Rename a folder and log it as info with [username]/[site_name] format"""
    try:
        if old_path.exists():
            old_path.rename(new_path)
            # Use provided username/site_name if available, else fallback to path parts
            if username and site_name:
                folder_str = f"{username}/{site_name}"
            else:
                folder_str = f"{get_relative_path(new_path)}"
            logger.info(f"Renamed site folder: {folder_str}")
            log_activity('Rename Folder', f"Renamed site folder: {folder_str}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to rename folder: {str(e)}")
        return False

def log_created_site_folder(username, site_name):
    folder_str = f"{username}/{site_name}"
    logger.info(f"Created site folder: {folder_str}")
    log_activity('Create Folder', f"Created site folder: {folder_str}")

@app.route('/api/verify-database', methods=['POST'])
def verify_database():
    """Verify and update database structure"""
    try:
        # Initialize database if needed
        if not os.path.exists(PATHS['DB_FILE']):
            db.initialize_database()
            return jsonify({'message': 'Database initialized'})

        # Load current database
        data = db.load_database()
        updated_sites = []

        # Check and update site IDs to 3 digits
        for upt_id, upt_data in data.get('upts', {}).items():
            for site in upt_data.get('sites', []):
                if len(site['id_perangkat']) < ID_FORMAT['SITE_ID_LENGTH']:
                    old_id = site['id_perangkat']
                    site['id_perangkat'] = site['id_perangkat'].zfill(ID_FORMAT['SITE_ID_LENGTH'])
                    updated_sites.append({
                        'old_id': old_id,
                        'new_id': site['id_perangkat']
                    })

        # Save updated database
        if updated_sites:
            db.save_database(data)

        # Verify folders
        created_folders = []
        for upt_id, upt_data in data.get('upts', {}).items():
            user_folder = Path(PATHS['USERDATA_DIR']) / upt_data['username']
            user_folder.mkdir(parents=True, exist_ok=True)
            
            for site in upt_data.get('sites', []):
                site_folder = user_folder / site['site_name']
                if not site_folder.exists():
                    site_folder.mkdir(parents=True, exist_ok=True)
                    created_folders.append(str(site_folder.relative_to(PATHS['USERDATA_DIR'])))

        return jsonify({
            'updated_sites': updated_sites,
            'created_folders': created_folders
        })

    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/direct/add-site', methods=['POST'])
@login_required
def direct_add_site():
    """Add a site directly to the JSON file"""
    data = validate_json_request()
    if not data:
        return jsonify({'error': 'Invalid JSON request'}), 400
        
    try:
        required_fields = ['id_upt', 'id_perangkat', 'site_name', 'token']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Read the JSON file directly
        db_path = PATHS['DB_FILE']
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            
        # Format IDs
        formatted_upt_id = data['id_upt'].zfill(ID_FORMAT['UPT_ID_LENGTH'])
        formatted_site_id = data['id_perangkat'].zfill(ID_FORMAT['SITE_ID_LENGTH'])
        
        # Check if UPT exists
        if formatted_upt_id not in db_data['upts']:
            return jsonify({'error': f"UPT with ID {formatted_upt_id} not found"}), 400
            
        # Check if site already exists
        for site in db_data['upts'][formatted_upt_id]['sites']:
            if site['id_perangkat'] == formatted_site_id:
                return jsonify({'error': f"Site with ID {formatted_site_id} already exists for UPT {formatted_upt_id}"}), 400
                
        # Create site folder
        username = db_data['upts'][formatted_upt_id]['username']
        site_name = data['site_name']
        site_folder = Path(PATHS['USERDATA_DIR']) / username / site_name
        site_folder.mkdir(parents=True, exist_ok=True)
        
        # Create required subfolders
        subfolders = ['health', 'spectrum', 'wifi_scan']
        for subfolder in subfolders:
            (site_folder / subfolder).mkdir(exist_ok=True)
            
        # Add site to JSON
        db_data['upts'][formatted_upt_id]['sites'].append({
            'id_perangkat': formatted_site_id,
            'site_name': site_name,
            'token': data['token']
        })
        
        # Write back to JSON file
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=4, ensure_ascii=False)
            
        log_activity('Add Site', f"Added new site - UPT ID: {formatted_upt_id}, Site Name: {site_name}, Device ID: {formatted_site_id}")
        return jsonify({'message': 'Site added successfully'})
    except Exception as e:
        logger.error(f"Error adding site directly: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/direct/update-site', methods=['POST'])
@login_required
def direct_update_site():
    """Update a site directly in the JSON file"""
    data = validate_json_request()
    if not data:
        return jsonify({'error': 'Invalid JSON request'}), 400
        
    try:
        required_fields = ['id_upt', 'id_perangkat']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Read the JSON file directly
        db_path = PATHS['DB_FILE']
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            
        # Format IDs
        formatted_upt_id = data['id_upt'].zfill(ID_FORMAT['UPT_ID_LENGTH'])
        formatted_site_id = data['id_perangkat'].zfill(ID_FORMAT['SITE_ID_LENGTH'])
        
        # Check if UPT exists
        if formatted_upt_id not in db_data['upts']:
            return jsonify({'error': f"UPT with ID {formatted_upt_id} not found"}), 400
            
        # Find and update the site
        site_found = False
        for site in db_data['upts'][formatted_upt_id]['sites']:
            if site['id_perangkat'] == formatted_site_id:
                site_found = True
                
                # Rename site folder if site name is changed
                if 'site_name' in data and data['site_name'] != site['site_name']:
                    username = db_data['upts'][formatted_upt_id]['username']
                    old_site_name = site['site_name']
                    new_site_name = data['site_name']
                    
                    old_path = Path(PATHS['USERDATA_DIR']) / username / old_site_name
                    new_path = Path(PATHS['USERDATA_DIR']) / username / new_site_name
                    
                    if old_path.exists():
                        old_path.rename(new_path)
                        logger.info(f"Renamed site folder from {old_path} to {new_path}")
                    
                    site['site_name'] = new_site_name
                
                # Update token if provided
                if 'token' in data:
                    site['token'] = data['token']
                
                break
                
        if not site_found:
            return jsonify({'error': f"Site with ID {formatted_site_id} not found for UPT {formatted_upt_id}"}), 400
            
        # Write back to JSON file
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=4, ensure_ascii=False)
            
        log_activity('Update Site', f"Updated site - UPT ID: {formatted_upt_id}, Device ID: {formatted_site_id}")
        return jsonify({'message': 'Site updated successfully'})
    except Exception as e:
        logger.error(f"Error updating site directly: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/direct/delete-site', methods=['POST'])
@login_required
def direct_delete_site():
    """Delete a site directly from the JSON file"""
    data = validate_json_request()
    if not data:
        return jsonify({'error': 'Invalid JSON request'}), 400
        
    try:
        required_fields = ['id_upt', 'id_perangkat']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Read the JSON file directly
        db_path = PATHS['DB_FILE']
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            
        # Format IDs
        formatted_upt_id = data['id_upt'].zfill(ID_FORMAT['UPT_ID_LENGTH'])
        formatted_site_id = data['id_perangkat'].zfill(ID_FORMAT['SITE_ID_LENGTH'])
        
        # Check if UPT exists
        if formatted_upt_id not in db_data['upts']:
            return jsonify({'error': f"UPT with ID {formatted_upt_id} not found"}), 400
            
        # Find and delete the site
        site_found = False
        for i, site in enumerate(db_data['upts'][formatted_upt_id]['sites']):
            if site['id_perangkat'] == formatted_site_id:
                site_found = True
                
                # Delete site folder
                username = db_data['upts'][formatted_upt_id]['username']
                site_name = site['site_name']
                site_folder = Path(PATHS['USERDATA_DIR']) / username / site_name
                
                if site_folder.exists():
                    import shutil
                    shutil.rmtree(site_folder)
                    logger.info(f"Deleted site folder: {site_folder}")
                
                # Remove site from JSON
                db_data['upts'][formatted_upt_id]['sites'].pop(i)
                break
                
        if not site_found:
            return jsonify({'error': f"Site with ID {formatted_site_id} not found for UPT {formatted_upt_id}"}), 400
            
        # Write back to JSON file
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(db_data, f, indent=4, ensure_ascii=False)
            
        log_activity('Delete Site', f"Deleted site - UPT ID: {formatted_upt_id}, Device ID: {formatted_site_id}")
        return jsonify({'message': 'Site deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting site directly: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/direct/read-sites', methods=['POST'])
@login_required
def direct_read_sites():
    """Read sites directly from the JSON file"""
    data = validate_json_request()
    if not data:
        return jsonify({'error': 'Invalid JSON request'}), 400
        
    try:
        required_fields = ['id_upt']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Read the JSON file directly
        db_path = PATHS['DB_FILE']
        with open(db_path, 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            
        # Format ID
        formatted_upt_id = data['id_upt'].zfill(ID_FORMAT['UPT_ID_LENGTH'])
        
        # Check if UPT exists
        if formatted_upt_id not in db_data['upts']:
            return jsonify({'error': f"UPT with ID {formatted_upt_id} not found"}), 400
            
        # Return sites
        return jsonify({'sites': db_data['upts'][formatted_upt_id]['sites']})
    except Exception as e:
        logger.error(f"Error reading sites directly: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/settings')
@login_required
def settings():
    """Show settings page"""
    return render_template('settings.html')

@app.route('/api/settings/language', methods=['GET'])
@login_required
def get_language():
    """Get current system language"""
    return jsonify({
        'language': session.get('language', 'en'),
        'available_languages': list(lang_manager.languages.keys())
    })

@app.route('/api/settings/language', methods=['PUT'])
@login_required
def update_language():
    """Update the system language"""
    try:
        data = validate_json_request()
        if not data or 'language' not in data:
            return jsonify({'error': lang_manager.get_text('settings.language_not_specified')}), 400
            
        if lang_manager.set_language(data['language']):
            session['language'] = data['language']
            return jsonify({'message': lang_manager.get_text('settings.save_success')})
        else:
            return jsonify({'error': lang_manager.get_text('settings.invalid_language')}), 400
    except Exception as e:
        logger.error(f"Error updating language: {str(e)}")
        return jsonify({'error': lang_manager.get_text('common.error')}), 500

@app.route('/api/settings/theme', methods=['GET'])
@login_required
def get_theme():
    """Get current system theme"""
    return jsonify({
        'theme': session.get('theme', 'light')
    })

@app.route('/api/settings/theme', methods=['PUT'])
@login_required
def update_theme():
    """Update the system theme"""
    try:
        data = validate_json_request()
        if not data or 'theme' not in data:
            return jsonify({'error': lang_manager.get_text('settings.theme_not_specified')}), 400
            
        valid_themes = ['light', 'dark', 'system']
        if data['theme'] not in valid_themes:
            return jsonify({'error': lang_manager.get_text('settings.invalid_theme')}), 400
            
        session['theme'] = data['theme']
        return jsonify({'message': lang_manager.get_text('settings.save_success')})
    except Exception as e:
        logger.error(f"Error updating theme: {str(e)}")
        return jsonify({'error': lang_manager.get_text('common.error')}), 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.context_processor
def inject_lang_manager():
    """Inject language manager into all templates"""
    return dict(lang_manager=lang_manager)

@app.route('/api/internal/validate-token', methods=['POST'])
@login_required
def internal_validate_token():
    """Internal API endpoint for salt-based token validation"""
    try:
        # Check if user is admin
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized access'}), 403
            
        data = validate_json_request()
        if not data or 'token' not in data:
            return jsonify({'error': 'Token is required'}), 400
            
        # Check if token contains any of the valid salts
        salt_used = None
        for salt in TOKEN_SALTS:
            if salt in data['token']:
                salt_used = salt
                break
                
        if not salt_used:
            return jsonify({'valid': False, 'message': 'Invalid token format'})
            
        # Validate the token
        if db.validate_one_time_token(data['token']):
            return jsonify({'valid': True, 'message': 'Token is valid'})
        else:
            return jsonify({'valid': False, 'message': 'Token is invalid or already used'})
            
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting MONSFER server...")
    logger.info(f"Debug mode: {app.debug}")
    logger.info(f"Running on {FLASK_CONFIG['HOST']}:{FLASK_CONFIG['PORT']}")
    app.run(
        host=FLASK_CONFIG['HOST'],
        port=int(FLASK_CONFIG['PORT']),
        debug=FLASK_CONFIG['DEBUG']
    )