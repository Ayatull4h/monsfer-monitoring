import os
import json
import shutil
from pathlib import Path
import logging

class FileManager:
    def __init__(self, userdata_path, base_userdata_dir):
        self.userdata_path = Path(userdata_path)
        self.base_userdata_dir = Path(base_userdata_dir)
        self.userdata = self._load_userdata()
        logging.info(f"FileManager initialized with userdata_path: {userdata_path}, base_userdata_dir: {base_userdata_dir}")
        
    def _load_userdata(self):
        """Load userdata from JSON file"""
        try:
            with open(self.userdata_path, 'r') as f:
                data = json.load(f)
                logging.info(f"Successfully loaded userdata from {self.userdata_path}")
                return data
        except Exception as e:
            logging.error(f"Error loading userdata from {self.userdata_path}: {str(e)}")
            return None
            
    def _parse_filename(self, filename):
        """Parse filename to extract upt_id, device_id, and timestamp"""
        try:
            # Split filename by underscore
            parts = filename.split('_')
            if len(parts) < 4:
                logging.error(f"Filename {filename} has insufficient parts (needs at least 4 parts)")
                return None, None, None
                
            # Extract upt_id and device_id from first part
            first_part = parts[0]
            upt_id = first_part[:2]
            device_id = first_part[2:]
            
            # Extract timestamp from last part
            timestamp = parts[-1]
            
            logging.info(f"Parsed filename {filename}: upt_id={upt_id}, device_id={device_id}, timestamp={timestamp}")
            return upt_id, device_id, timestamp
        except Exception as e:
            logging.error(f"Error parsing filename {filename}: {str(e)}")
            return None, None, None
            
    def _get_user_info(self, upt_id, device_id):
        """Get username and site_name from userdata based on upt_id and device_id"""
        try:
            if not self.userdata or 'upts' not in self.userdata:
                logging.error("Userdata is empty or missing 'upts' key")
                return None, None
                
            upt_info = self.userdata['upts'].get(upt_id)
            if not upt_info:
                logging.error(f"No UPT info found for upt_id {upt_id}")
                return None, None
                
            username = upt_info.get('username')
            if not username:
                logging.error(f"No username found for upt_id {upt_id}")
                return None, None
                
            # Find matching site
            for site in upt_info.get('sites', []):
                if site.get('id_perangkat') == device_id:
                    site_name = site.get('site_name')
                    logging.info(f"Found matching site for upt_id {upt_id}, device_id {device_id}: username={username}, site_name={site_name}")
                    return username, site_name
                    
            logging.error(f"No matching site found for upt_id {upt_id}, device_id {device_id}")
            return username, None
        except Exception as e:
            logging.error(f"Error getting user info for upt_id {upt_id}, device_id {device_id}: {str(e)}")
            return None, None
            
    def organize_file(self, file_path):
        """Organize file based on naming convention"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logging.error(f"File not found: {file_path}")
                return False
                
            filename = file_path.name
            upt_id, device_id, timestamp = self._parse_filename(filename)
            
            if not all([upt_id, device_id, timestamp]):
                logging.error(f"Invalid filename format: {filename}")
                return False
                
            username, site_name = self._get_user_info(upt_id, device_id)
            if not username or not site_name:
                logging.error(f"User info not found for upt_id {upt_id}, device_id {device_id}")
                return False
                
            # Determine subfolder based on filename content
            if 'MONITORING' in filename:
                subfolder = 'spectrum'
            elif 'WIFI' in filename:
                subfolder = 'wifi'
            elif 'HEALTH' in filename:
                subfolder = 'health'
            else:
                subfolder = 'other'
            
            # Create target directory
            target_dir = self.base_userdata_dir / username / site_name / subfolder
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # New filename is the original filename to preserve uniqueness
            new_filename = filename
            
            # Move file to target directory
            target_path = target_dir / new_filename
            try:
                shutil.move(str(file_path), str(target_path))
                logging.info(f"File organized: {filename} -> {target_path}")
                return True
            except Exception as e:
                logging.error(f"Error moving file from {file_path} to {target_path}: {str(e)}")
                return False
            
        except Exception as e:
            logging.error(f"Error organizing file {file_path}: {str(e)}")
            return False 