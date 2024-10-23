import logging
from ig_gs_handling import IgGSHandling

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    account_id = "JK"  # Replace with the actual account ID
    handler = IgGSHandling(account_id)

    logger.info("Starting Instagram Google Sheets handling process")

    if not handler.authenticate_and_setup():
        logger.error("Failed to authenticate and set up. Exiting.")
        return

    logger.info("Authentication and setup successful")

    # Update location IDs
    logger.info("Updating location IDs")
    handler.update_location_ids()
    logger.info("Location ID update complete")

    # Update music track IDs
    logger.info("Updating music track IDs")
    handler.update_music_track_ids()
    logger.info("Music track ID update complete")

    # Update media paths
    logger.info("Updating media paths")
    handler.update_media_paths()
    logger.info("Media path update complete")

    logger.info("Instagram Google Sheets handling process completed successfully")

if __name__ == "__main__":
    main()
