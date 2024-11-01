import json
import logging
import os
import pytz
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union, cast
import time

from googleapiclient.discovery import Resource, build
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
import traceback

# Type aliases for Google services
SheetsService = Any  # Type for sheets.spreadsheets()
DriveService = Any  # Type for drive.files()


# More specific type hints for Google services
class GoogleSheetsResource:
    """Type hint class for Google Sheets API."""

    def values(self) -> Any: ...
    def get(self, spreadsheetId: str, range: str, **kwargs) -> Dict[str, Any]: ...
    def batchUpdate(
        self, spreadsheetId: str, body: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]: ...


class GoogleDriveResource:
    """Type hint class for Google Drive API."""

    def list(self, q: str, fields: str, **kwargs) -> Dict[str, Any]: ...
    def get_media(self, fileId: str, **kwargs) -> Any: ...
    def get(self, fileId: str, fields: str, **kwargs) -> Dict[str, Any]: ...


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class GoogleSheetsHandler:
    """Handles interactions with Google Sheets."""

    account_id: str
    spreadsheet_id: Optional[str] = None
    sheets_service: Optional[GoogleSheetsResource] = None
    drive_service: Optional[GoogleDriveResource] = None
    credentials: Optional[Credentials] = None
    token_file: Optional[str] = None
    creds_file: str = "credentials.json"
    folder_id: Optional[str] = None
    scopes: List[str] = field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
    )

    def __post_init__(self) -> None:
        """Initialize after dataclass fields are set."""
        self.token_file = self.get_token_file()

    def get_token_file(self) -> Optional[str]:
        """Get configuration file path from environment variables."""
        config_env = f"GOOGLE_SHEETS_CONFIG_{self.account_id.upper()}"
        config_path = os.getenv(config_env)

        logger.debug(f"Looking for config file using env var: {config_env}")
        logger.debug(f"Config path: {config_path}")

        if not config_path or not os.path.exists(config_path):
            logger.error(f"Config file not found at: {config_path}")
            raise ValueError(f"Please set {config_env} to point to your config file")

        logger.debug(f"Found config file at: {config_path}")
        return config_path

    def authenticate(self) -> None:
        """Authenticate with Google APIs using config file."""
        try:
            logger.debug("Starting authentication process")

            if not self.token_file:
                raise ValueError("No config file path available")

            # Load credentials from config file
            with open(self.token_file, "r") as f:
                config = json.load(f)
                logger.debug(f"Loaded config with keys: {list(config.keys())}")

                # Create credentials object properly
                creds_dict = {
                    'token': str(config.get('token')),
                    'refresh_token': str(config.get('refresh_token')),
                    'token_uri': str(config.get('token_uri', 'https://oauth2.googleapis.com/token')),
                    'client_id': str(config.get('client_id')),
                    'client_secret': str(config.get('client_secret')),
                    'scopes': config.get('scopes'),
                }

                self.credentials = Credentials.from_authorized_user_info(
                    info=creds_dict,
                    scopes=self.scopes
                )

                # Handle expiry if present
                if 'expiry' in config:
                    self.credentials._expires = config['expiry']

            # Build services
            sheets = build("sheets", "v4", credentials=self.credentials)
            drive = build("drive", "v3", credentials=self.credentials)
            
            self.sheets_service = sheets.spreadsheets()
            self.drive_service = drive.files()

            logger.info("Successfully authenticated with Google services")

            # Initialize spreadsheet ID if needed
            if not self.spreadsheet_id:
                folder_name = "ig JK tests"
                self.folder_id = self.get_folder_id(folder_name)
                if self.folder_id:
                    spreadsheet_name = f"{self.account_id} IG input table"
                    self.spreadsheet_id = self.find_file_id(
                        self.folder_id, spreadsheet_name
                    )
                    if not self.spreadsheet_id:
                        logger.error(f"Could not find spreadsheet: {spreadsheet_name}")
                    else:
                        logger.info(f"Found spreadsheet: {self.spreadsheet_id}")
                else:
                    logger.error(f"Could not find folder: {folder_name}")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.sheets_service = None
            self.drive_service = None
            raise

    def get_folder_id(self, folder_name: str) -> Optional[str]:
        """Get the ID of a folder by its name."""
        try:
            logger.debug(f"Looking for folder: '{folder_name}'")
            logger.debug(f"Current working directory: {os.getcwd()}")
            
            # First try exact path in My Drive
            query = (
                "mimeType='application/vnd.google-apps.folder' and "
                f"name='{folder_name}' and "
                "'root' in parents and "
                "trashed=false"
            )
            
            logger.debug(f"Using query: {query}")
            
            results = self.drive_service.list(
                q=query,
                fields="files(id, name, parents)",
                spaces='drive',
                pageSize=1  # We only need one result
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                logger.info(f"Found folder '{folder_name}' in My Drive with ID: {folder_id}")
                return folder_id
            else:
                # If not found in root, try searching everywhere
                query = (
                    "mimeType='application/vnd.google-apps.folder' and "
                    f"name='{folder_name}' and "
                    "trashed=false"
                )
                
                logger.debug(f"Trying broader search with query: {query}")
                
                results = self.drive_service.list(
                    q=query,
                    fields="files(id, name, parents)",
                    spaces='drive',
                    pageSize=1
                ).execute()
                
                items = results.get('files', [])
                if items:
                    folder_id = items[0]['id']
                    logger.info(f"Found folder '{folder_name}' with ID: {folder_id}")
                    return folder_id
                
                logger.error(f"Folder '{folder_name}' not found in Google Drive")
                logger.error("Please check:")
                logger.error("1. The folder exists in your Google Drive")
                logger.error("2. You have access permissions to the folder")
                logger.error("3. The folder name is exactly 'ig JK tests' (case sensitive)")
                return None

        except Exception as e:
            logger.error(f"Error getting folder ID: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def find_file_id(self, folder_id: str, file_name: str) -> Optional[str]:
        """Find a file's ID by its name within a specific folder."""
        try:
            query = f"'{folder_id}' in parents and name='{file_name}'"
            results = self.drive_service.list(
                q=query, fields="files(id, name)"
            ).execute()
            items = results.get("files", [])

            if not items:
                logger.error(f"File '{file_name}' not found in folder {folder_id}")
                return None

            file_id = items[0]["id"]
            logger.debug(f"Found file ID: {file_id} for file: {file_name}")
            return file_id

        except Exception as e:
            logger.error(f"Error finding file ID: {e}")
            return None

    def read_spreadsheet(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """Read data from a Google Spreadsheet."""
        try:
            result = (
                self.sheets_service.values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get("values", [])
            logger.debug(f"Read {len(values)} rows from spreadsheet")
            return values

        except Exception as e:
            logger.error(f"Error reading spreadsheet: {e}")
            return []

    def batch_update(self, spreadsheet_id: str, data: List[Dict[str, Any]]) -> bool:
        """Perform a batch update on a Google Spreadsheet with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not spreadsheet_id:
                    raise ValueError("Missing required parameter 'spreadsheet_id'")

                body = {
                    "valueInputOption": "USER_ENTERED",
                    "data": [
                        {"range": item["range"], "values": item["values"]}
                        for item in data
                    ],
                }

                result = (
                    self.sheets_service.values()
                    .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                    .execute()
                )

                logger.debug(f"Batch update completed: {result}")
                return True

            except Exception as e:
                logger.error(
                    f"Error performing batch update (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                    try:
                        self.authenticate()  # Try to re-authenticate
                    except Exception as auth_e:
                        logger.error(f"Re-authentication failed: {auth_e}")
                else:
                    return False

    def verify_file_exists(self, file_id: str) -> bool:
        """
        Verify that a file exists and is accessible without downloading it.
        
        Args:
            file_id (str): The Google Drive file ID
            
        Returns:
            bool: True if file exists and is accessible, False otherwise
        """
        try:
            # Just get metadata to verify access
            file = self.drive_service.get(
                fileId=file_id,
                fields='id, name, mimeType'
            ).execute()
            
            logger.debug(f"Verified access to file: {file.get('name')} ({file.get('mimeType')})")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying file {file_id}: {e}")
            return False
