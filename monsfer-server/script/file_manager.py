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
        
    def _load_userdata(self):
        """Load userdata from JSON file"""
        try:
            with open(self.userdata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading userdata: {str(e)}")
            return None
            
    def _parse_filename(self, filename):
        """Parse filename to extract upt_id, device_id, and timestamp"""
        try:
            # Split filename by underscore
            parts = filename.split('_')
            if len(parts) < 4:
                return None, None, None
                
            # Extract upt_id and device_id from first part
            first_part = parts[0]
            upt_id = first_part[:2]
            device_id = first_part[2:]
            
            # Extract timestamp from last part
            timestamp = parts[-2] + "_"+ parts[-1]
            
            return upt_id, device_id, timestamp
        except Exception as e:
            logging.error(f"Error parsing filename {filename}: {str(e)}")
            return None, None, None
            
    def _get_user_info(self, upt_id, device_id):
        """Get username and site_name from userdata based on upt_id and device_id"""
        try:
            if not self.userdata or 'upts' not in self.userdata:
                return None, None
                
            upt_info = self.userdata['upts'].get(upt_id)
            if not upt_info:
                return None, None
                
            username = upt_info.get('username')
            if not username:
                return None, None
                
            # Find matching site
            for site in upt_info.get('sites', []):
                if site.get('id_perangkat') == device_id:
                    return username, site.get('site_name')
                    
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
            
            # New filename preserves original extension
            new_filename = filename
            
            # Move file to target directory
            target_path = target_dir / new_filename
            shutil.move(str(file_path), str(target_path))
            
            logging.info(f"File organized: {filename} -> {target_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error organizing file {file_path}: {str(e)}")
            return False 