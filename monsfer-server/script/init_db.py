import os
import logging
from pathlib import Path
from db_operations import DatabaseOperations
from config import PATHS, LOG_CONFIG, ADMIN_CONFIG

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    filename=PATHS['APP_LOG']
)
logger = logging.getLogger(__name__)

def init_database() -> bool:
    """Initialize the database with default admin user
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Initialize database
        db = DatabaseOperations()
        
        # Create admin user if not exists
        if not db.verify_admin(ADMIN_CONFIG['USERNAME'], ADMIN_CONFIG['PASSWORD']):
            # Update admin settings
            db.update_admin_settings(
                ADMIN_CONFIG['USERNAME'],
                ADMIN_CONFIG['PASSWORD'],
                ADMIN_CONFIG['FULLNAME']
            )
            logger.info("Database initialized successfully")
            logger.info(f"Admin user created with username: {ADMIN_CONFIG['USERNAME']}")
            print("Database initialized successfully")
            print(f"Admin user created with username: {ADMIN_CONFIG['USERNAME']}")
            return True
        else:
            logger.info("Database already initialized")
            print("Database already initialized")
            return True
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database() 