from flask import Blueprint, request, jsonify
from functools import wraps
from typing import Dict, Any, Optional
from db_operations import DatabaseOperations
from logging_config import LoggingConfig

upt_bp = Blueprint('upt', __name__)
db = DatabaseOperations()
logger = LoggingConfig()

def validate_json_request() -> Optional[Dict[str, Any]]:
    """Validate JSON request and return data"""
    if not request.is_json:
        return None
    return request.get_json()

@upt_bp.route('/api/upts', methods=['GET', 'POST'])
def manage_upts():
    """Handle UPT operations"""
    try:
        if request.method == 'GET':
            # Get all UPTs
            upts = db.get_all_upts()
            return jsonify({'success': True, 'upts': upts})
            
        elif request.method == 'POST':
            # Create new UPT
            data = validate_json_request()
            if not data:
                return jsonify({'error': 'Invalid JSON request'}), 400
                
            required_fields = ['id_upt', 'fullname', 'username', 'password']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Create UPT in database
            db.create_upt(
                data['id_upt'],
                data['fullname'],
                data['username'],
                data['password']
            )
            
            logger.log_activity('UPT Created', 
                              f"New UPT created - ID: {data['id_upt']}, Name: {data['fullname']}")
            
            return jsonify({'success': True, 'message': 'UPT created successfully'})
            
    except Exception as e:
        logger.log_error(f"Error managing UPTs: {str(e)}")
        return jsonify({'error': 'Failed to manage UPTs'}), 500

@upt_bp.route('/api/upts/<id_upt>', methods=['PUT', 'DELETE'])
def manage_upt(id_upt: str):
    """Handle individual UPT operations"""
    try:
        if request.method == 'PUT':
            # Update UPT
            data = validate_json_request()
            if not data:
                return jsonify({'error': 'Invalid JSON request'}), 400
                
            required_fields = ['fullname', 'username', 'password']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Update UPT in database
            db.update_upt(
                id_upt,
                data['fullname'],
                data['username'],
                data['password']
            )
            
            logger.log_activity('UPT Updated', 
                              f"UPT updated - ID: {id_upt}, Name: {data['fullname']}")
            
            return jsonify({'success': True, 'message': 'UPT updated successfully'})
            
        elif request.method == 'DELETE':
            # Delete UPT
            db.delete_upt(id_upt)
            
            logger.log_activity('UPT Deleted', 
                              f"UPT deleted - ID: {id_upt}")
            
            return jsonify({'success': True, 'message': 'UPT deleted successfully'})
            
    except Exception as e:
        logger.log_error(f"Error managing UPT: {str(e)}")
        return jsonify({'error': 'Failed to manage UPT'}), 500

@upt_bp.route('/api/upts/<id_upt>/sites', methods=['GET', 'POST'])
def manage_upt_sites(id_upt: str):
    """Handle UPT site operations"""
    try:
        if request.method == 'GET':
            # Get all sites for UPT
            sites = db.get_upt_sites(id_upt)
            return jsonify({'success': True, 'sites': sites})
            
        elif request.method == 'POST':
            # Add new site to UPT
            data = validate_json_request()
            if not data:
                return jsonify({'error': 'Invalid JSON request'}), 400
                
            required_fields = ['id_perangkat', 'site_name', 'token']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
                
            # Add site to UPT in database
            db.add_upt_site(
                id_upt,
                data['id_perangkat'],
                data['site_name'],
                data['token']
            )
            
            logger.log_activity('Site Added', 
                              f"New site added to UPT - UPT ID: {id_upt}, Site: {data['site_name']}")
            
            return jsonify({'success': True, 'message': 'Site added successfully'})
            
    except Exception as e:
        logger.log_error(f"Error managing UPT sites: {str(e)}")
        return jsonify({'error': 'Failed to manage UPT sites'}), 500

@upt_bp.route('/api/upts/<id_upt>/sites/<id_perangkat>', methods=['PUT', 'DELETE'])
def manage_upt_site(id_upt: str, id_perangkat: str):
    """Handle individual UPT site operations"""
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
            db.update_upt_site(
                id_upt,
                id_perangkat,
                data['site_name'],
                data['token']
            )
            
            logger.log_activity('Site Updated', 
                              f"Site updated - UPT ID: {id_upt}, Site ID: {id_perangkat}")
            
            return jsonify({'success': True, 'message': 'Site updated successfully'})
            
        elif request.method == 'DELETE':
            # Delete site
            db.delete_upt_site(id_upt, id_perangkat)
            
            logger.log_activity('Site Deleted', 
                              f"Site deleted - UPT ID: {id_upt}, Site ID: {id_perangkat}")
            
            return jsonify({'success': True, 'message': 'Site deleted successfully'})
            
    except Exception as e:
        logger.log_error(f"Error managing UPT site: {str(e)}")
        return jsonify({'error': 'Failed to manage UPT site'}), 500 