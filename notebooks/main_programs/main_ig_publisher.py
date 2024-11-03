"""
Main script for running the Instagram content publisher.
"""

import logging
import argparse
import sys
from pathlib import Path
import traceback

from ig_content_publisher import IgContentPublisher
from ig_client import IgClient
from html_filter import NoHTMLFilter

# Add the src directory to Python path
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

# Add filter to root logger
logging.getLogger().addFilter(NoHTMLFilter())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main(account_id: str):
    """
    Main function to process and publish Instagram content.
    
    Args:
        account_id (str): The Instagram account identifier
    """
    publisher = None
    try:
        logger.info(f"Starting Instagram content publishing process for account: {account_id}")

        # Initialize content publisher
        try:
            publisher = IgContentPublisher(account_id)
            logger.info("Content publisher initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content publisher: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return

        # Verify Instagram health before proceeding
        try:
            if not publisher.verify_instagram_health():
                logger.error("Instagram health check failed. Exiting.")
                return
            logger.info("Instagram health check passed")
        except Exception as e:
            logger.error(f"Error during Instagram health check: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return

        # Process pending content
        while True:
            try:
                publisher.process_pending_content()
            except Exception as e:
                logger.error(f"Error processing content: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                if input("\nDo you want to continue despite the error? (y/N): ").lower() != "y":
                    break
            
            # Ask if user wants to process more content
            if input("\nDo you want to process more content? (y/N): ").lower() != "y":
                break

        logger.info("Content publishing process completed")

    except Exception as e:
        logger.error(f"Error in publishing process: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        if publisher:
            try:
                publisher.cleanup()
                logger.info("Cleanup completed successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
        logger.info("Exiting program...")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python main_ig_publisher.py <account_id>")
        sys.exit(1)
    
    account_id = sys.argv[1]
    main(account_id)
