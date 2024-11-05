"""
Main program for handling Instagram Google Sheets operations and proxy management.
"""

import warnings
import logging
import traceback
from pathlib import Path
from ig_gs_handling import IgGSHandling
from proxy_manager import ProxyManager
from typing import Optional, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def handle_google_sheets(account_id: str) -> bool:
    """
    Handle Google Sheets operations.
    
    Args:
        account_id (str): The Instagram account identifier
        
    Returns:
        bool: True if all operations completed successfully
    """
    logger.info(f"Starting Google Sheets handling for account: {account_id}")
    try:
        handler = IgGSHandling(account_id)
        logger.info("IgGSHandling instance created successfully")
        
        if not handler.authenticate_and_setup():
            logger.error("Failed to authenticate and set up. Exiting.")
            return False
            
        operations = {
            "update_location_ids": handler.update_location_ids,
            "update_music_track_ids": handler.update_music_track_ids,
            "update_media_paths": handler.update_media_paths,
            "sync_google_sheet_with_db": handler.sync_google_sheet_with_db
        }
        
        for operation_name, operation_func in operations.items():
            try:
                logger.info(f"Starting {operation_name}...")
                operation_func()
                logger.info(f"Successfully completed {operation_name}")
            except Exception as e:
                logger.error(f"Error during {operation_name}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error in Google Sheets handling: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_proxy_connection(proxy_manager: ProxyManager) -> bool:
    """
    Test proxy connection and location.
    
    Args:
        proxy_manager: ProxyManager instance
        
    Returns:
        bool: True if connection is valid and in correct location
    """
    if proxy_manager.validate_connection():
        logger.info("✅ Proxy connection validated successfully")
        return True
    else:
        logger.error("❌ Proxy validation failed")
        return False

def main():
    """Main execution function."""
    account_id = "JK"
    
    # Initialize proxy manager
    proxy_manager = ProxyManager()
    
    # Test proxy connection
    if test_proxy_connection(proxy_manager):
        # Proceed with Google Sheets operations
        if handle_google_sheets(account_id):
            logger.info("✅ Google Sheets operations completed successfully")
        else:
            logger.error("❌ Google Sheets operations failed")
    else:
        logger.error("❌ Proxy connection test failed")

if __name__ == "__main__":
    main()
