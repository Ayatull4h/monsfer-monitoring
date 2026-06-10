from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Dict, Any, Optional
from db_operations import DatabaseOperations
from logging_config import LoggingConfig

site_bp = Blueprint('site', __name__)
db = DatabaseOperations()
logger = LoggingConfig()

def validate_json_request() -> Optional[Dict[str, Any]]:
    """Validate JSON request and return data"""
    if not request.is_json:
        return None
    return request.get_json()

@site_bp.route('/api/sites', methods=['GET', 'POST'])
def manage_sites():
    """Handle site operations"""
    try:
        if request.method == 'GET':
            # Get all sites
            sites = db.get_all_sites()
            return jsonify({'success': True, 'sites': sites})
            
        elif request.method == 'POST':
            # Create new site
            data = validate_json_request()
            if not data:
                return jsonify({'error': 'Invalid JSON request'}), 400
                
            required_fields = ['id_perangkat', 'site_name', 'token']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Create site in database
            db.create_site(
                data['id_perangkat'],
                data['site_name'],
                data['token']
            )
            
            logger.log_activity('Site Created', 
                              f"New site created - ID: {data['id_perangkat']}, Name: {data['site_name']}")
            
            return jsonify({'success': True, 'message': 'Site created successfully'})
            
    except Exception as e:
        logger.log_error(f"Error managing sites: {str(e)}")
        return jsonify({'error': 'Failed to manage sites'}), 500

@site_bp.route('/api/sites/<id_perangkat>', methods=['PUT', 'DELETE'])
def manage_site(id_perangkat: str):
    """Handle individual site operations"""
    try:
        if request.method == 'PUT':
            # Update site
            data = validate_json_request()
            if not data:
                return jsonify({'error': 'Invalid JSON request'}), 400
                
            required_fields = ['site_name', 'token']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Update site in database
            db.update_site(
                id_perangkat,
                data['site_name'],
                data['token']
            )
            
            logger.log_activity('Site Updated', 
                              f"Site updated - ID: {id_perangkat}, Name: {data['site_name']}")
            
            return jsonify({'success': True, 'message': 'Site updated successfully'})
            
        elif request.method == 'DELETE':
            # Delete site
            db.delete_site(id_perangkat)
            
            logger.log_activity('Site Deleted', 
                              f"Site deleted - ID: {id_perangkat}")
            
            return jsonify({'success': True, 'message': 'Site deleted successfully'})
            
    except Exception as e:
        logger.log_error(f"Error managing site: {str(e)}")
        return jsonify({'error': 'Failed to manage site'}), 500

@site_bp.route('/api/sites/<id_perangkat>/status', methods=['GET'])
def get_site_status(id_perangkat: str):
    """Get site status"""
    try:
        status = db.get_site_status(id_perangkat)
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        logger.log_error(f"Error getting site status: {str(e)}")
        return jsonify({'error': 'Failed to get site status'}), 500

@site_bp.route('/api/sites/<id_perangkat>/logs', methods=['GET'])
def get_site_logs(id_perangkat: str):
    """Get site logs"""
    try:
        logs = db.get_site_logs(id_perangkat)
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        logger.log_error(f"Error getting site logs: {str(e)}")
        return jsonify({'error': 'Failed to get site logs'}), 500 