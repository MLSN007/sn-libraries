import warnings

warnings.filterwarnings(
    "ignore", message="file_cache is unavailable when using oauth2client >= 4.0.0"
)
import logging
from ig_gs_handling import IgGSHandling

logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set logging level for google_sheets_handler to DEBUG
logging.getLogger("google_sheets_handler").setLevel(logging.DEBUG)


def main():
    account_id = "JK"  # Replace with the actual account ID
    logger.info(
        f"Starting Instagram Google Sheets handling process for account: {account_id}"
    )

    try:
        handler = IgGSHandling(account_id)
        logger.info("IgGSHandling instance created successfully")
    except Exception as e:
        logger.error(f"Failed to create IgGSHandling instance: {str(e)}")
        return

    try:
        logger.info("Attempting to authenticate and set up...")
        if not handler.authenticate_and_setup():
            logger.error("Failed to authenticate and set up. Exiting.")
            return
        logger.info("Authentication and setup successful")
    except Exception as e:
        logger.error(f"Error during authentication and setup: {str(e)}")
        return

    try:
        logger.info("Updating location IDs")
        handler.update_location_ids()
        logger.info("Location ID update complete")
    except Exception as e:
        logger.error(f"Error updating location IDs: {str(e)}")

    try:
        logger.info("Updating music track IDs")
        handler.update_music_track_ids()
        logger.info("Music track ID update complete")
    except Exception as e:
        logger.error(f"Error updating music track IDs: {str(e)}")

    try:
        logger.info("Updating media paths")
        handler.update_media_paths()
        logger.info("Media path update complete")
    except Exception as e:
        logger.error(f"Error updating media paths: {str(e)}")

    logger.info("Instagram Google Sheets handling process completed")


if __name__ == "__main__":
    main()
