"""
Main script for running the Instagram content publisher.
"""

import logging
import argparse
import re
import traceback
import sys
import signal
import os
from typing import Optional, Any
from types import FrameType
from ig_content_publisher import IgContentPublisher


# Add this filter class
class NoHTMLFilter(logging.Filter):
    HTML_PATTERNS = [
        r"<[^>]+>",  # HTML tags
        r"<script.*?</script>",  # Script tags
        r"<!DOCTYPE.*?>",  # Doctype declarations
    ]

    def filter(self, record):
        message = str(record.msg)
        return not any(re.search(pattern, message) for pattern in self.HTML_PATTERNS)


# Modify the logging setup
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add filter to root logger
logging.getLogger().addFilter(NoHTMLFilter())

logger = logging.getLogger(__name__)


def validate_account_id(account_id: str) -> bool:
    """Validate that the account ID exists and is properly formatted."""
    if not account_id or not isinstance(account_id, str):
        return False
    # Add additional validation logic
    return True


# Global variable for the publisher
publisher: Optional[IgContentPublisher] = None


def signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """Handle shutdown signals."""
    global publisher
    logger.info("Received shutdown signal. Cleaning up...")
    if publisher:
        publisher.cleanup()  # type: ignore
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main(account_id: str):
    """Main function to process and publish Instagram content."""
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

        # Verify Instagram health and proxy before proceeding
        try:
            if not publisher.verify_instagram_health():
                logger.error("Instagram health check or proxy verification failed. Exiting.")
                return
            logger.info("Instagram health check and proxy verification passed")
        except Exception as e:
            logger.error(f"Error during health check: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return

        # Rest of the code remains the same...


if __name__ == "__main__":
    main()
