import json
import os
import logging
from typing import Dict, Any, Optional
from config.config_loader import config

def get_user_data(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user data from userdata.json using username
    
    Args:
        username: Username to search for
        
    Returns:
        If user found:
            For admin: {'username': username, 'is_admin': True}
            For UPT: {'id_upt': upt_id, 'fullname': fullname, 'username': username, 'sites': sites}
        If user not found: None
    """
    try:
        # Get absolute path to userdata.json from config
        json_path = config.USERDATA_PATH
        
        # Load userdata.json
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check admin
        if username == 'admin' and 'admin' in data:
            admin = data['admin']
            return {
                'username': username,
                'is_admin': True
            }
        
        # Check UPTs
        if 'upts' in data:
            for upt_id, upt in data['upts'].items():
                if upt['username'] == username:
                    return {
                        'id_upt': upt_id,
                        'fullname': upt.get('fullname', ''),
                        'username': username,
                        'sites': upt.get('sites', [])
                    }
        
        logging.warning(f"No user found with username: {username}")
        return None
        
    except FileNotFoundError:
        logging.error(f"Userdata file not found at: {config.USERDATA_PATH}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in userdata file: {config.USERDATA_PATH}")
        return None
    except Exception as e:
        logging.error(f"Error getting user data: {str(e)}")
        return None

def main():
    """Command line interface"""
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        handlers=[logging.StreamHandler()]
    )
    
    parser = argparse.ArgumentParser(description='Get user data from userdata.json')
    parser.add_argument('username', help='Username to search for')
    
    args = parser.parse_args()
    
    result = get_user_data(args.username)
    
    if result:
        if isinstance(result, dict):
            if result.get('is_admin'):
                print(f"Found admin user: {result['username']}")
            else:
                print(f"Found UPT user:")
                print(f"ID UPT: {result['id_upt']}")
                print(f"Fullname: {result['fullname']}")
                print(f"Username: {result['username']}")
                print(f"Sites: {result['sites']}")
    else:
        print(f"No user found with username: {args.username}")

if __name__ == "__main__":
    main() 