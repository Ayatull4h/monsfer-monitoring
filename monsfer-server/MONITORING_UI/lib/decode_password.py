import hashlib
import argparse
import json
import os
import logging
from typing import Optional, Dict, Any, Union
from config.config_loader import config

class PasswordHandler:
    """Simple password encoding and decoding module"""
    
    def __init__(self, hash_algorithm: str = 'sha256'):
        """
        Initialize password handler
        
        Args:
            hash_algorithm: Hash algorithm to use (default: sha256)
        """
        self.hash_algorithm = hash_algorithm
        
    def encode(self, password: str, salt: str = "") -> str:
        """
        Encode password using hash algorithm
        
        Args:
            password: Password to encode
            salt: Salt to add to password (optional)
            
        Returns:
            Encoded password as hex string
        """
        hasher = hashlib.new(self.hash_algorithm)
        hasher.update((password + salt).encode())
        return hasher.hexdigest()
        
    def decode(self, stored_hash: str, password: str, salt: str = "") -> bool:
        """
        Verify if password matches stored hash
        
        Args:
            stored_hash: Stored hash to compare against
            password: Password to verify
            salt: Salt used in original hash (optional)
            
        Returns:
            True if password matches, False otherwise
        """
        return self.encode(password, salt) == stored_hash

    def decode_from_json(self, json_path: str, username: str, password: str) -> Union[Dict[str, Any], bool]:
        """
        Decode password from userdata.json
        
        Args:
            json_path: Path to userdata.json
            username: Username to check
            password: Password to verify
            
        Returns:
            If password matches:
                For admin: {'username': username, 'is_admin': True}
                For UPT: {'id_upt': upt_id, 'fullname': fullname, 'username': username, 'sites': sites}
            If password doesn't match: False
        """
        try:
            # Load userdata.json
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check admin
            if username == 'admin' and 'admin' in data:
                admin = data['admin']
                stored_hash = admin['password']
                salt = admin.get('salt', '')
                if self.decode(stored_hash, password, salt):
                    return {
                        'username': username,
                        'is_admin': True
                    }
            
            # Check UPTs
            if 'upts' in data:
                for upt_id, upt in data['upts'].items():
                    if upt['username'] == username:
                        stored_hash = upt['password']
                        salt = upt.get('salt', '')
                        if self.decode(stored_hash, password, salt):
                            return {
                                'id_upt': upt_id,
                                'fullname': upt.get('fullname', ''),
                                'username': username,
                                'sites': upt.get('sites', [])
                            }
            
            logging.warning(f"Password verification failed for user: {username}")
            return False
            
        except FileNotFoundError:
            logging.error(f"Userdata file not found at: {json_path}")
            return False
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format in userdata file: {json_path}")
            return False
        except Exception as e:
            logging.error(f"Error decoding password: {str(e)}")
            return False

def main():
    """Command line interface"""
    # Configure logging
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format=config.LOG_FORMAT,
        handlers=[logging.StreamHandler()]
    )
    
    parser = argparse.ArgumentParser(description='Password encoding and verification tool')
    
    # Add global arguments
    parser.add_argument('-a', '--algorithm', default='sha256', help='Hash algorithm to use (default: sha256)')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Encode command
    encode_parser = subparsers.add_parser('encode', help='Encode a password')
    encode_parser.add_argument('password', help='Password to encode')
    encode_parser.add_argument('-s', '--salt', default='', help='Salt to use (optional)')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a password')
    verify_parser.add_argument('stored_hash', help='Stored hash to verify against')
    verify_parser.add_argument('password', help='Password to verify')
    verify_parser.add_argument('-s', '--salt', default='', help='Salt used in original hash (optional)')
    
    # Decode from JSON command
    decode_parser = subparsers.add_parser('decode', help='Decode password from userdata.json')
    decode_parser.add_argument('json_path', help='Path to userdata.json')
    decode_parser.add_argument('username', help='Username to check')
    decode_parser.add_argument('password', help='Password to verify')
    
    args = parser.parse_args()
    
    # Create handler instance
    handler = PasswordHandler(hash_algorithm=args.algorithm)
    
    if args.command == 'encode':
        encoded = handler.encode(args.password, args.salt)
        print(f"\nPassword: {args.password}")
        print(f"Salt: {args.salt}")
        print(f"Algorithm: {args.algorithm}")
        print(f"Encoded: {encoded}")
        
    elif args.command == 'verify':
        is_valid = handler.decode(args.stored_hash, args.password, args.salt)
        print(f"\nStored Hash: {args.stored_hash}")
        print(f"Password: {args.password}")
        print(f"Salt: {args.salt}")
        print(f"Algorithm: {args.algorithm}")
        print(f"Result: {'✓ Match' if is_valid else '✗ No match'}")
        
    elif args.command == 'decode':
        result = handler.decode_from_json(args.json_path, args.username, args.password)
        print(f"\nUsername: {args.username}")
        print(f"Password: {args.password}")
        if result:
            if isinstance(result, dict):
                if result.get('is_admin'):
                    print(f"Result: ✓ Success (Admin user)")
                else:
                    print(f"Result: ✓ Success")
                    print(f"UPT ID: {result['id_upt']}")
                    print(f"Fullname: {result['fullname']}")
                    print(f"Username: {result['username']}")
                    print(f"Sites: {result['sites']}")
            else:
                print(f"Result: ✓ Success")
        else:
            print(f"Result: ✗ Failed")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
