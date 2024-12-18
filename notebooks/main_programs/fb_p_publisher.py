from fb_config_loader import FbConfigLoader
from fb_api_client import FbApiClient
from fb_post_tracker import FbPostTracker
from fb_post_manager import FbPostManager
from fb_post_composer import FbPostComposer
from fb_publishing_orchestrator import FbPublishingOrchestrator
from error_handler import setup_logging, handle_error
from google_sheets_handler import GoogleSheetsHandler
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any

logger = logging.getLogger(__name__)


@handle_error
def main() -> None:
    """
    Main function to orchestrate the publishing of Facebook posts and tracking via Google Sheets.
    """
    setup_logging()

    # -------------------------------------------------------------------------
    # Load configuration for FB user+page
    config_file = r"C:\Users\manue\Documents\GitHub007\sn-libraries\config_files\FB_JK_JK Travel_JK Travel_config.json"
    config_loader = FbConfigLoader(config_file)
    logger.info("Facebook configuration and credentials loaded successfully")

    # -------------------------------------------------------------------------
    # Set up Google Sheets configuration -------------------------------------
    account_id = "JK"
    spreadsheet_id = "1wrvG3wmptA76kywbVe1gy5as-ALDzmebLvqoxWIw9mw"
    logger.info(
        f"Google Sheets configuration - Account ID: {account_id}, Spreadsheet ID: {spreadsheet_id}"
    )

    # Define the source path for media files
    source_path = r"C:\Users\manue\Downloads\tests"
    logger.info(f"Source path for media files: {source_path}")
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------

    # Initialize components
    api_client = FbApiClient(config_loader.credentials)
    sheets_handler = GoogleSheetsHandler(
        account_id=account_id, use_oauth=False  # Set use_oauth to False for development mode
    )
    try:
        sheets_handler.authenticate()
    except ValueError as e:
        logger.error(f"Authentication error: {str(e)}")
        return
    post_tracker = FbPostTracker(account_id, spreadsheet_id)
    post_composer = FbPostComposer(source_path)
    post_manager = FbPostManager(api_client, post_composer)

    # Pass the page_id to the orchestrator
    page_id = config_loader.credentials.get("page_id")
    if not page_id:
        raise ValueError("page_id not found in the configuration")

    orchestrator = FbPublishingOrchestrator(post_tracker, post_manager, page_id)

    try:
        # Publish next post
        result = orchestrator.publish_next_post()
        if result:
            logger.info(f"Post published successfully. Result: {result}")
        else:
            logger.warning("No post was available to publish.")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()

