import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from functools import wraps
from config import PATHS, LOG_CONFIG

class SecureDataManager:
    def __init__(self):
        """Initialize secure data manager"""
        self.db_file = PATHS['DB_FILE']
        self.logger = logging.getLogger('secure_data')
        self.initialize_logging()
        
    def initialize_logging(self):
        """Initialize logging for security events"""
        handler = logging.FileHandler('logs/security.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def load_data(self) -> Optional[Dict[str, Any]]:
        """Securely load data from JSON file"""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error loading data: {str(e)}")
            return None
            
    def save_data(self, data: Dict[str, Any]) -> bool:
        """Securely save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            return False
            
    def get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user data without exposing sensitive information"""
        data = self.load_data()
        if not data:
            return None
            
        if username in data.get('upts', {}):
            user_data = data['upts'][username].copy()
            # Remove sensitive data
            user_data.pop('password', None)
            user_data.pop('salt', None)
            return user_data
            
        return None
        
    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        data = self.load_data()
        if not data:
            return False
            
        if username in data.get('upts', {}):
            user_data = data['upts'][username]
            stored_password = user_data.get('password', '')
            salt = user_data.get('salt', '')
            
            # Verify password using the stored salt
            hashed_password = self._hash_password(password, salt)
            return hashed_password == stored_password
            
        return False
        
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt"""
        import hashlib
        return hashlib.sha256((password + salt).encode()).hexdigest()
        
    def update_user_data(self, username: str, new_data: Dict[str, Any]) -> bool:
        """Update user data with validation"""
        data = self.load_data()
        if not data or username not in data.get('upts', {}):
            return False
            
        # Validate new data
        if not self._validate_user_data(new_data):
            return False
            
        # Update only allowed fields
        allowed_fields = ['fullname', 'settings']
        current_data = data['upts'][username]
        
        for field in allowed_fields:
            if field in new_data:
                current_data[field] = new_data[field]
                
        return self.save_data(data)
        
    def _validate_user_data(self, data: Dict[str, Any]) -> bool:
        """Validate user data structure"""
        required_fields = ['fullname']
        return all(field in data for field in required_fields)
        
    def log_security_event(self, event_type: str, username: str, details: str):
        """Log security-related events"""
        self.logger.info(f"{event_type} - User: {username} - {details}")
        
# Create a singleton instance
secure_data_manager = SecureDataManager() 