from flask import Blueprint, request, jsonify, session, redirect, url_for, flash, render_template
from functools import wraps
from typing import Dict, Any, Optional
from db_operations import DatabaseOperations
from logging_config import LoggingConfig

admin_bp = Blueprint('admin', __name__)
db = DatabaseOperations()
logger = LoggingConfig()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_json_request() -> Optional[Dict[str, Any]]:
    """Validate JSON request and return data"""
    if not request.is_json:
        return None
    return request.get_json()

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        try:
            if db.verify_admin(username, password):
                session['admin_logged_in'] = True
                session['username'] = username
                logger.log_activity('Login', 'Successful login')
                flash('Login successful!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                logger.log_activity('Login', 'Failed login attempt', username)
                flash('Invalid username or password', 'error')
        except Exception as e:
            logger.log_error(f"Login error: {str(e)}")
            flash('An error occurred during login', 'error')
            
    return render_template('login.html')

@admin_bp.route('/logout')
def logout():
    """Handle logout"""
    logger.log_activity('Logout', 'User logged out')
    session.pop('admin_logged_in', None)
    session.pop('username', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Show dashboard with UPTs"""
    try:
        upts = db.get_all_upts()
        admin_settings = db.get_admin_settings()
        
        return render_template('dashboard.html', 
                             upts=upts, 
                             admin_config={
                                 'USERNAME': admin_settings['username'],
                                 'FULLNAME': admin_settings['fullname']
                             })
    except Exception as e:
        logger.log_error(f"Dashboard error: {str(e)}")
        session.pop('admin_logged_in', None)  # Clear session on error
        flash('An error occurred while loading the dashboard', 'error')
        return redirect(url_for('admin.login'))

@admin_bp.route('/api/admin/settings', methods=['PUT'])
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
        
        logger.log_activity('Settings Update', 
                          f"Admin settings updated - Username: {data['username']}, Fullname: {data['fullname']}")
        
        return jsonify({'success': True, 'message': 'Settings updated successfully'})
        
    except Exception as e:
        logger.log_error(f"Error updating admin settings: {str(e)}")
        return jsonify({'error': 'Failed to update settings'}), 500 