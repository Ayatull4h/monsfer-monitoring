import json
import os
import logging
import hashlib
import secrets
from pathlib import Path
from config import PATHS, LOG_CONFIG, ID_FORMAT, TOKEN_SALTS
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    filename=PATHS['APP_LOG']
)
logger = logging.getLogger(__name__)

class DatabaseOperations:
    def __init__(self):
        """Initialize database operations with JSON file"""
        self.db_file = PATHS['DB_FILE']
        self.token_file = os.path.join(os.path.dirname(PATHS['DB_FILE']), 'tokenlist.json')
        self.initialize_database()
        self.initialize_token_database()
    
    def load_database(self):
        """Load data from JSON file"""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {str(e)}")
            return None
            
    def save_database(self, data):
        """Save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving database: {str(e)}")
            return False

    def load_token_database(self):
        """Load token data from JSON file"""
        try:
            with open(self.token_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding token JSON: {str(e)}")
            return None
            
    def save_token_database(self, data):
        """Save token data to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving token database: {str(e)}")
            return False
            
    def initialize_database(self):
        """Initialize database if it doesn't exist"""
        if not os.path.exists(self.db_file):
            initial_data = {
                "admin": {
                    "username": "admin",
                    "password": "",
                    "salt": "",
                    "settings": {}
                },
                "upts": {}
            }
            self.save_database(initial_data)

    def initialize_token_database(self):
        """Initialize token database if it doesn't exist"""
        if not os.path.exists(self.token_file):
            initial_data = {
                "tokens": {}
            }
            self.save_token_database(initial_data)
            
    def format_id(self, id_type, number):
        """Format ID with proper padding"""
        if id_type == "upt":
            return f"UPT{str(number).zfill(3)}"
        elif id_type == "site":
            return f"SITE{str(number).zfill(4)}"
        return str(number)
        
    def get_admin_settings(self):
        """Get admin settings from the database"""
        try:
            data = self.load_database()
            if not data or "admin" not in data:
                return None
                
            admin = data["admin"]
            return {
                "username": admin.get("username", ""),
                "fullname": admin.get("fullname", "System Administrator"),
                "settings": admin.get("settings", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting admin settings: {str(e)}")
            return None
            
    def get_all_upts(self):
        """Get all UPTs from the database"""
        try:
            data = self.load_database()
            if not data or "upts" not in data:
                return []
                
            # Convert UPT dictionary to list and add ID
            upts = []
            for upt_id, upt_data in data["upts"].items():
                upt_data["id_upt"] = upt_id
                upts.append(upt_data)
                
            return upts
            
        except Exception as e:
            logger.error(f"Error getting UPTs: {str(e)}")
            return []
            
    def get_sanitized_upts(self):
        """Get all UPTs with sensitive information removed"""
        try:
            upts = self.get_all_upts()
            sanitized_upts = []
            
            for upt in upts:
                sanitized_upt = {
                    'id_upt': upt['id_upt'],
                    'fullname': upt['fullname'],
                    'username': upt['username'],
                    'sites': upt['sites']
                }
                sanitized_upts.append(sanitized_upt)
                
            return sanitized_upts
            
        except Exception as e:
            logger.error(f"Error getting sanitized UPTs: {str(e)}")
            return []
            
    def add_upt(self, id_upt, fullname, username, password):
        """Add a new UPT to the database"""
        try:
            logger.info(f"Attempting to add UPT with ID: {id_upt}")
            data = self.load_database()
            if not data:
                logger.error("Failed to load database")
                return False
                
            logger.info("Database loaded successfully")
            logger.info(f"Current database structure: {json.dumps(data, indent=2)}")
                
            # Format UPT ID
            formatted_id = id_upt.zfill(ID_FORMAT['UPT_ID_LENGTH'])
            logger.info(f"Formatted UPT ID: {formatted_id}")
            
            # Check if UPT already exists
            if formatted_id in data["upts"]:
                logger.error(f"UPT with ID {formatted_id} already exists")
                raise ValueError(f"UPT with ID {formatted_id} already exists")
                
            # Generate salt and hash password
            salt = secrets.token_hex(16)
            hashed = hashlib.sha256((password + salt).encode()).hexdigest()
            logger.info("Password hashed successfully")
            
            # Add new UPT
            data["upts"][formatted_id] = {
                "id_upt": formatted_id,
                "fullname": fullname,
                "username": username,
                "password": hashed,
                "salt": salt,
                "sites": []
            }
            logger.info("New UPT data prepared")
            
            result = self.save_database(data)
            if result:
                logger.info("UPT added successfully")
            else:
                logger.error("Failed to save database after adding UPT")
            return result
            
        except Exception as e:
            logger.error(f"Error adding UPT: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            return False
            
    def update_upt(self, id_upt, fullname, username, password=None):
        """Update an existing UPT"""
        try:
            data = self.load_database()
            if not data:
                return False
                
            # Format UPT ID
            formatted_id = id_upt.zfill(ID_FORMAT['UPT_ID_LENGTH'])
            
            # Check if UPT exists
            if formatted_id not in data["upts"]:
                raise ValueError(f"UPT with ID {formatted_id} not found")
                
            # Update UPT data
            data["upts"][formatted_id]["fullname"] = fullname
            data["upts"][formatted_id]["username"] = username
            
            # Update password if provided
            if password:
                salt = secrets.token_hex(16)
                hashed = hashlib.sha256((password + salt).encode()).hexdigest()
                data["upts"][formatted_id]["password"] = hashed
                data["upts"][formatted_id]["salt"] = salt
                
            return self.save_database(data)
            
        except Exception as e:
            logger.error(f"Error updating UPT: {str(e)}")
            return False
            
    def delete_upt(self, id_upt):
        """Delete an UPT from the database"""
        try:
            data = self.load_database()
            if not data:
                return False
                
            # Format UPT ID
            formatted_id = id_upt.zfill(ID_FORMAT['UPT_ID_LENGTH'])
            
            # Check if UPT exists
            if formatted_id not in data["upts"]:
                raise ValueError(f"UPT with ID {formatted_id} not found")
                
            # Delete UPT
            del data["upts"][formatted_id]
            
            return self.save_database(data)
            
        except Exception as e:
            logger.error(f"Error deleting UPT: {str(e)}")
            return False
            
    def verify_admin(self, username, password):
        
        """Verify admin credentials"""
        try:
            data = self.load_database()
            if not data or "admin" not in data:
                return False
                
            admin = data["admin"]
            if admin["username"] != username:
                return False
                
            # If no salt, use direct comparison (for backward compatibility)
            if not admin.get("salt"):
                stored_hash = hashlib.sha256(password.encode()).hexdigest()
                stored_hash = password
                return admin["password"] == stored_hash
                
            # With salt, hash password+salt
            salt = admin["salt"]
            # logger.error(username,password,hashed,salt)
            hashed = hashlib.sha256((password + salt).encode()).hexdigest()
            # hashed = password
            print(username,password,admin["password"],hashed)
            return admin["password"] == hashed
            
        except Exception as e:
            logger.error(f"Error verifying admin: {str(e)}")
            return False
            
    def update_all_passwords_with_salt(self):
        """Update all passwords to use salt"""
        data = self.load_database()
        if not data:
            return False
            
        updated = False
        
        # Update admin password if needed
        if "admin" in data and not data["admin"].get("salt"):
            salt = secrets.token_hex(16)
            password = data["admin"]["password"]
            if password:
                hashed = hashlib.sha256((password + salt).encode()).hexdigest()
                data["admin"]["password"] = hashed
                data["admin"]["salt"] = salt
                updated = True
                
        # Update UPT passwords if needed
        if "upts" in data:
            for upt_id, upt_data in data["upts"].items():
                if not upt_data.get("salt"):
                    salt = secrets.token_hex(16)
                    password = upt_data.get("password", "")
                    if password:
                        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
                        upt_data["password"] = hashed
                        upt_data["salt"] = salt
                        updated = True
                        
        if updated:
            return self.save_database(data)
        return False
        
    def update_admin_settings(self, username, password, fullname="admin"):
        """Update admin settings with salted password"""
        data = self.load_database()
        if not data:
            return False
            
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        # hashed = password
        
        data["admin"]["username"] = username
        data["admin"]["password"] = hashed
        data["admin"]["salt"] = salt
        data["admin"]["fullname"] = fullname
        
        return self.save_database(data)

    def cleanup_expired_tokens(self, data):
        """Remove tokens that are older than 10 seconds"""
        try:
            current_time = datetime.now()
            expired_tokens = []
            
            for token, token_data in data['tokens'].items():
                created_at = datetime.fromisoformat(token_data['created_at'])
                if (current_time - created_at) > timedelta(seconds=10):
                    expired_tokens.append(token)
            
            # Remove expired tokens
            for token in expired_tokens:
                del data['tokens'][token]
            
            if expired_tokens:
                logger.info(f"Removed {len(expired_tokens)} expired tokens")
                self.save_token_database(data)
            
            return data
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return data

    def generate_one_time_token(self):
        """Generate a one-time use token"""
        try:
            # Generate random token (32 bytes)
            token = secrets.token_urlsafe(32)
            
            # Select a random salt from TOKEN_SALTS
            salt = secrets.choice(TOKEN_SALTS)
            
            data = self.load_token_database()
            if not data:
                return None
                
            # Clean up expired tokens before adding new one
            data = self.cleanup_expired_tokens(data)
                
            # Add token to database with used=False and store salt internally
            data['tokens'][token] = {
                'used': False,
                'created_at': datetime.now().isoformat(),
                'salt': salt  # Store salt internally
            }
            
            if self.save_token_database(data):
                return token
            return None
            
        except Exception as e:
            logger.error(f"Error generating token: {str(e)}")
            return None
            
    def validate_one_time_token(self, token):
        """Validate a one-time use token"""
        try:
            data = self.load_token_database()
            if not data or 'tokens' not in data:
                logger.warning("Token validation failed: No token database found")
                return False
                
            # Clean up expired tokens before validation
            data = self.cleanup_expired_tokens(data)
                
            if token not in data['tokens']:
                logger.warning(f"Token validation failed: Token not found in database")
                return False
                
            token_data = data['tokens'][token]
            
            # Get the stored salt
            stored_salt = token_data.get('salt')
            if not stored_salt:
                logger.warning("Token validation failed: No salt found for token")
                return False
                
            # Check if token is already used
            if token_data['used']:
                logger.warning("Token validation failed: Token already used")
                return False
                
            # Mark token as used
            token_data['used'] = True
            if self.save_token_database(data):
                logger.info("Token validation successful")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return False 