from fb_config_loader import FbConfigLoader
from fb_api_client import FbApiClient
from fb_post_tracker import FbPostTracker
from fb_post_manager import FbPostManager
from fb_post_composer import FbPostComposer
from fb_publishing_orchestrator import FbPublishingOrchestrator
from error_handler import setup_logging, handle_error
from google_sheets_handler import GoogleSheetsHandler
import logging

logger = logging.getLogger(__name__)


@handle_error
def main():
    setup_logging()

    # Load configuration for FB user+page --------------COMMENT OUT THE RIGHT FB USER_APP_PG ---------------
    # config_file = r"C:\Users\manue\Documents\GitHub007\sn-libraries\config_files\FB_LS_M001_ES_config.json"
    config_file = r"C:\Users\manue\Documents\GitHub007\sn-libraries\config_files\FB_JK_JK Travel_JK Travel_config.json"

    config_loader = FbConfigLoader(config_file)

    # Set up Google Sheets configuration -----------COMMENT OUT THE RIGHT GOOGLE USER -------------
    # JK
    account_id = "JK"  # the account id for Google Sheets
    spreadsheet_id = "1wrvG3wmptA76kywbVe1gy5as-ALDzmebLvqoxWIw9mw"

    # NOCA
    # account_id = "NOCA"
    # spreadsheet_id = "1gNaLWtTnQzuUyRnwp1RGcoXoOeLiapef4oKEof3WUek"

    print(
        f"Google Sheets configuration - Account ID: {account_id}, Spreadsheet ID: {spreadsheet_id}"
    )

    # -------------------------------------------------------------------------

    # Define the source path for media files
    source_path = r"C:\Users\manue\Downloads\tests"
    print(f"Source path for media files: {source_path}")

    # Initialize components
    api_client = FbApiClient(config_loader.credentials)
    sheets_handler = GoogleSheetsHandler(account_id=account_id)
    sheets_handler.authenticate()
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
        orchestrator.publish_next_post()

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
