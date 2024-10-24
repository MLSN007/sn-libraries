import logging
import random
from typing import Optional
from google_sheets_handler import GoogleSheetsHandler
from ig_utils import IgUtils
from ig_client import IgClient

logging.basicConfig(level=logging.DEBUG)  # Change level to DEBUG
logger = logging.getLogger(__name__)


class IgGSHandling:
    """Handles Instagram Google Sheets operations."""

    def __init__(self, account_id: str, folder_name: str = "ig JK tests"):
        """
        Initialize the IgGSHandling class.

        Args:
            account_id (str): The Instagram account identifier.
            folder_name (str): The name of the Google Drive folder containing the spreadsheet and media files.
        """
        self.account_id = account_id
        self.folder_name = folder_name
        self.gs_handler = GoogleSheetsHandler(account_id)
        try:
            self.ig_client = IgClient(account_id)
            self.ig_utils = IgUtils(self.ig_client.client)
        except Exception as e:
            logger.error(f"Error initializing IgClient or IgUtils: {str(e)}")
            raise
        self.spreadsheet_id: Optional[str] = None
        self.folder_id: Optional[str] = None

    def authenticate_and_setup(self) -> bool:
        try:
            self.gs_handler.authenticate()
            logger.info("Authentication successful")

            # Check permissions
            if not self.gs_handler.check_permissions():
                logger.error("Failed to check permissions")
                return False
            logger.info("Permissions check successful")

            # Get folder ID
            self.folder_id = self.gs_handler.get_folder_id(self.folder_name)
            if not self.folder_id:
                logger.error(f"Folder '{self.folder_name}' not found. Please check the folder name and permissions.")
                return False
            logger.info(f"Folder ID retrieved: {self.folder_id}")

            spreadsheet_name = f"ig {self.account_id} Post table"
            spreadsheets = self.gs_handler.read_spreadsheet(
                self.folder_id, f"name = '{spreadsheet_name}'"
            )
            if spreadsheets and len(spreadsheets) > 0:
                self.spreadsheet_id = spreadsheets[0]["id"]
            else:
                logger.error(
                    f"Spreadsheet '{spreadsheet_name}' not found in folder '{self.folder_name}'"
                )
                return False

            logger.info(
                f"Successfully set up with folder ID: {self.folder_id} and spreadsheet ID: {self.spreadsheet_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error during authentication and setup: {str(e)}")
            return False

    def update_location_ids(self):
        """Update location IDs for rows with location_str but no location_id."""
        logger.info("Updating location IDs...")
        data = self.gs_handler.read_spreadsheet(self.spreadsheet_id, "A:N")
        if not data:
            logger.error("Failed to read spreadsheet data")
            return

        header = data[0]
        location_str_index = header.index("location_str")
        location_id_index = header.index("location_id")
        content_id_index = header.index("content_id")

        updates = []
        for row_index, row in enumerate(data[1:], start=2):
            if row[content_id_index]:  # Skip published content
                continue
            if row[location_str_index] and not row[location_id_index]:
                locations = self.ig_utils.get_top_locations_by_name(
                    row[location_str_index]
                )
                if locations:
                    location_id = locations[0].pk
                    updates.append(
                        {"range": f"N{row_index}", "values": [[location_id]]}
                    )
                    logger.info(
                        f"Updated location ID for row {row_index}: {location_id}"
                    )

        if updates:
            self.gs_handler.batch_update(self.spreadsheet_id, updates)
            logger.info(f"Updated {len(updates)} location IDs")
        else:
            logger.info("No location IDs to update")

    def update_music_track_ids(self):
        """Update music track IDs for rows with music_reference but no music_track_id."""
        logger.info("Updating music track IDs...")
        data = self.gs_handler.read_spreadsheet(self.spreadsheet_id, "A:O")
        if not data:
            logger.error("Failed to read spreadsheet data")
            return

        header = data[0]
        music_reference_index = header.index("music_reference")
        music_track_id_index = header.index("music_track_id")
        content_id_index = header.index("content_id")

        updates = []
        for row_index, row in enumerate(data[1:], start=2):
            if row[content_id_index]:  # Skip published content
                continue
            if row[music_reference_index] and not row[music_track_id_index]:
                tracks = self.ig_utils.music_search(row[music_reference_index])
                if tracks:
                    track = random.choice(tracks[:3])  # Random selection from top 3
                    music_track_id = track.id
                    updates.append(
                        {"range": f"O{row_index}", "values": [[music_track_id]]}
                    )
                    logger.info(
                        f"Updated music track ID for row {row_index}: {music_track_id}"
                    )

        if updates:
            self.gs_handler.batch_update(self.spreadsheet_id, updates)
            logger.info(f"Updated {len(updates)} music track IDs")
        else:
            logger.info("No music track IDs to update")

    def update_media_paths(self):
        """Update media_paths for rows with media_file_names but no media_paths."""
        logger.info("Updating media paths...")
        data = self.gs_handler.read_spreadsheet(self.spreadsheet_id, "A:P")
        if not data:
            logger.error("Failed to read spreadsheet data")
            return

        header = data[0]
        media_file_names_index = header.index("media_file_names")
        media_paths_index = header.index("media_paths")
        content_id_index = header.index("content_id")

        updates = []
        for row_index, row in enumerate(data[1:], start=2):
            if row[content_id_index]:  # Skip published content
                continue
            if row[media_file_names_index] and not row[media_paths_index]:
                file_names = row[media_file_names_index].split(",")
                file_ids = []
                for file_name in file_names:
                    file_id = self.gs_handler.find_file_id(
                        self.folder_id, file_name.strip()
                    )
                    if file_id:
                        file_ids.append(file_id)
                if file_ids:
                    media_paths = ",".join(file_ids)
                    updates.append(
                        {"range": f"P{row_index}", "values": [[media_paths]]}
                    )
                    logger.info(
                        f"Updated media paths for row {row_index}: {media_paths}"
                    )

        if updates:
            self.gs_handler.batch_update(self.spreadsheet_id, updates)
            logger.info(f"Updated {len(updates)} media paths")
        else:
            logger.info("No media paths to update")
