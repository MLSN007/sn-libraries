import warnings
import logging
import traceback
from ig_gs_handling import IgGSHandling
from html_filter import NoHTMLFilter

# Suppress google auth warnings
warnings.filterwarnings(
    "ignore", message="file_cache is unavailable when using oauth2client >= 4.0.0"
)

# Configure logging with our filter
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Add filter to root logger
logging.getLogger().addFilter(NoHTMLFilter())

# Set specific loggers to INFO level
logging.getLogger("google_sheets_handler").setLevel(logging.INFO)
logging.getLogger("instagrapi").setLevel(logging.WARNING)
logging.getLogger("private_request").setLevel(logging.WARNING)
logging.getLogger("public_request").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
# Set logging level for google_sheets_handler to DEBUG
logging.getLogger("google_sheets_handler").setLevel(logging.DEBUG)


def main():
    account_id = "JK"
    logger.info(
        f"Starting Instagram Google Sheets handling process for account: {account_id}"
    )

    try:
        handler = IgGSHandling(account_id)
        logger.info("IgGSHandling instance created successfully")
    except Exception as e:
        logger.error(f"Failed to create IgGSHandling instance: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return

    try:
        logger.info("Attempting to authenticate and set up...")
        if not handler.authenticate_and_setup():
            logger.error("Failed to authenticate and set up. Exiting.")
            return
        logger.info("Authentication and setup successful")
    except Exception as e:
        logger.error(f"Error during authentication and setup: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return

    # Uncomment and run the corresponding sessions (here or the one below)
    # operations = {
    #     "update_location_ids": handler.update_location_ids,
    #     "update_music_track_ids": handler.update_music_track_ids,
    #     "update_media_paths": handler.update_media_paths,
    # }

    # Uncomment and run these sections one at a time as needed
    operations = {
        "update_media_paths": handler.update_media_paths,
        "sync_google_sheet_with_db": handler.sync_google_sheet_with_db,
    }

    for operation_name, operation_func in operations.items():
        try:
            logger.info(f"Starting {operation_name}...")
            operation_func()
            logger.info(f"Successfully completed {operation_name}")
        except Exception as e:
            logger.error(f"Error during {operation_name}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Ask user if they want to continue with next operation
            if input(f"\nContinue with remaining operations? (y/N): ").lower() != "y":
                logger.info("Stopping process as requested by user")
                break

    logger.info("Instagram Google Sheets handling process completed")


if __name__ == "__main__":
    main()
