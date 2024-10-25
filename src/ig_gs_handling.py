import logging
import random
from typing import Optional
from google_sheets_handler import GoogleSheetsHandler
from ig_utils import IgUtils, get_db_connection
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
        db_path = f"C:/Users/manue/Documents/GitHub007/sn-libraries/data/{account_id}_ig.db"
        self.db_connection = get_db_connection(db_path)
        if not self.db_connection:
            raise Exception("Failed to connect to the database.")
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
                logger.error(
                    f"Folder '{self.folder_name}' not found. Please check the folder name and permissions."
                )
                return False
            logger.info(f"Folder ID retrieved: {self.folder_id}")

            spreadsheet_name = f"{self.account_id} IG input table"
            # Find the spreadsheet ID within the folder
            self.spreadsheet_id = self.gs_handler.find_file_id(
                self.folder_id, spreadsheet_name
            )
            if not self.spreadsheet_id:
                logger.error(
                    f"Spreadsheet '{spreadsheet_name}' not found in folder '{self.folder_name}'"
                )
                return False

            # Set the spreadsheet_id in GoogleSheetsHandler
            self.gs_handler.spreadsheet_id = self.spreadsheet_id

            # Now you can read the spreadsheet data
            spreadsheets = self.gs_handler.read_spreadsheet(
                self.spreadsheet_id,
                "'Ig Origin Data'!A:R",  # Or the actual range you want to read
            )
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
        data = self.gs_handler.read_spreadsheet(self.spreadsheet_id, "A:S")
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
                print(
                    f"\n\n LOCATION STR: {row[location_str_index]} ---- on ROW: {row_index} \n\n"
                )
                locations = self.ig_utils.get_top_locations_by_name(
                    row[location_str_index]
                )
                if locations:
                    location_id = locations[0].pk
                    print(f"\n\n LOCATION ID: {location_id} \n\n")
                    updates.append(
                        {"range": f"J{row_index}", "values": [[location_id]]}
                    )
                    logger.info(
                        f"Updated location ID for row {row_index}: {location_id}"
                    )

        if updates:
            print("\n\n LOCATION IDS UPDATES", updates, "\n\n")
            self.gs_handler.batch_update(self.spreadsheet_id, updates)
            logger.info(f"Updated {len(updates)} location IDs")
        else:
            logger.info("No location IDs to update")

    def update_music_track_ids(self):
        """Update music track IDs for rows with music_reference but no music_track_id."""
        logger.info("Updating music track IDs...")
        data = self.gs_handler.read_spreadsheet(self.spreadsheet_id, "A:S")
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
                        {"range": f"L{row_index}", "values": [[music_track_id]]}
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
        data = self.gs_handler.read_spreadsheet(self.spreadsheet_id, "A:S")
        if not data:
            logger.error("Failed to read spreadsheet data")
            return

        header = data[0]
        media_file_names_index = header.index("media_file_names")
        media_paths_index = header.index("media_paths")
        content_id_index = header.index("content_id")
        print(f"MEDIA FILE NAMES INDEX: {media_file_names_index}")
        print(f"MEDIA PATHS INDEX: {media_paths_index}")
        print(f"CONTENT ID INDEX: {content_id_index}")

        updates = []
        for row_index, row in enumerate(data[1:], start=2):
            print(f"\n ROW: {row}    ROW INDEX: {row_index} \n")
            if row[content_id_index]:  # Skip published content
                continue
            if row[media_file_names_index] and not row[media_paths_index]:
                file_names = row[media_file_names_index].split(",")
                print(f"\n\n FILE NAMES: {file_names} \n\n")
                file_ids = []
                for file_name in file_names:
                    file_id = self.gs_handler.find_file_id(
                        self.folder_id, file_name.strip()
                    )
                    if file_id:
                        file_ids.append(file_id)
                if file_ids:
                    print(f"\n\n FILE IDS: {file_ids} \n\n")
                    media_paths = ",".join(file_ids)
                    updates.append(
                        {"range": f"N{row_index}", "values": [[media_paths]]}
                    )
                    logger.info(
                        f"Updated media paths for row {row_index}: {media_paths}"
                    )

        if updates:
            print(updates)
            self.gs_handler.batch_update(self.spreadsheet_id, updates)
            logger.info(f"Updated {len(updates)} media paths")
        else:
            logger.info("No media paths to update")

    def sync_google_sheet_with_db(self) -> None:
        """
        Syncs the Google Sheet with the SQLite database by uploading new entries
        and updating the Google Sheet with generated content IDs.
        """
        # Fetch rows without content_id
        rows = self.gs_handler.get_rows_without_content_id()

        # Insert rows into the database and get content_ids
        content_ids = []
        for row in rows:
            content_id = self.insert_into_db(row)
            content_ids.append(content_id)

        # Update Google Sheet with content_ids
        self.gs_handler.update_content_ids(rows, content_ids)

    def insert_into_db(self, row: dict) -> int:
        """
        Inserts a row into the SQLite database and returns the generated content_id.

        Args:
            row (dict): A dictionary representing a row from the Google Sheet.

        Returns:
            int: The generated content_id from the database.
        """
        print("INSERTING INTO DB", row, "\n")
        cursor = self.db_connection.cursor()
        cursor.execute(
            """
            INSERT INTO content (content_type, media_type, title, caption, hashtags, mentions, location_id, music_track_id, media_file_names, media_paths, link, publish_date, publish_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("content_type"),
                row.get("media_type"),
                row.get("title"),
                row.get("caption"),
                row.get("hashtags"),
                row.get("mentions"),
                row.get("location_id"),  # Ensure this matches the table schema
                row.get("music_track_id"),
                row.get("media_file_names"),
                row.get("media_paths"),
                row.get("link"),
                row.get("publish_date"),
                row.get("publish_time"),
                row.get("status"),
            ),
        )
        self.db_connection.commit()
        return cursor.lastrowid

