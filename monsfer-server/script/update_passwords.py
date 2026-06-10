import logging
from pathlib import Path
from db_operations import DatabaseOperations
from config import LOG_CONFIG, PATHS

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_CONFIG['level']),
    format=LOG_CONFIG['format'],
    filename=PATHS['APP_LOG']
)
logger = logging.getLogger(__name__)

def update_passwords():
    """Update all existing passwords to use salt"""
    try:
        # Initialize database operations
        db = DatabaseOperations()
        
        # Update all passwords with salt
        if db.update_all_passwords_with_salt():
            print("Successfully updated all passwords with salt")
            logger.info("Successfully updated all passwords with salt")
        else:
            print("No passwords needed updating")
            logger.info("No passwords needed updating")
            
    except Exception as e:
        print(f"Error updating passwords: {str(e)}")
        logger.error(f"Error updating passwords: {str(e)}")
        logger.exception("Full traceback:")

if __name__ == "__main__":
    update_passwords() 