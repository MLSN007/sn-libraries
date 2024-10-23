import json
import logging
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.transport.requests

logger = logging.getLogger(__name__)


@dataclass
class GoogleSheetsHandler:
    """
    Handles interactions with Google Sheets and Drive APIs for multiple accounts.

    This class supports two modes of operation:
    1. Development mode: Uses local configuration files for credentials.
    2. Production mode: Uses the full OAuth 2.0 flow for desktop applications.

    Usage:
    - For development: handler = GoogleSheetsHandler('account1')
    - For production: handler = GoogleSheetsHandler('account1', use_oauth=True)

    Note: To create the initial config_account_XX.json file, use the initial_setup.py script.
    This script will guide you through the OAuth flow and create the necessary configuration file.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self, account_id: str, use_oauth: bool = False):
        """
        Initialize the GoogleSheetsHandler.

        Args:
            account_id (str): Identifier for the Google account to use.
            use_oauth (bool): If True, use OAuth flow instead of config file.
        """

        self.account_id = account_id
        self.use_oauth = use_oauth
        self.config_path = self._get_config_path()
        self.creds: Optional[Credentials] = None
        self.sheets_service: Optional[Any] = None
        self.drive_service: Optional[Any] = None

    def _get_config_path(self) -> Optional[str]:
        """Get the configuration file path from environment variables."""
        # Convert account_id to upper case to ensure consistency in environment variable names

        env_var = f"GOOGLE_SHEETS_CONFIG_{self.account_id.upper()}"
        config_path = os.getenv(env_var)
        if not self.use_oauth and not config_path:
            raise ValueError(f"Environment variable {env_var} is not set")
        return config_path

    def authenticate(self) -> None:
        """
        Authenticate with Google APIs.

        This method handles authentication for both development and production modes:
        - In development mode, it loads credentials from the config file.
        - In production mode, it uses the full OAuth 2.0 flow.

        The method also refreshes expired tokens and saves new tokens in development mode.
        """
        if not self.use_oauth and self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
            if "token" in config:
                token_data = config["token"]
                if isinstance(token_data, str):
                    token_data = json.loads(token_data)
                if isinstance(token_data, dict):
                    self.creds = Credentials.from_authorized_user_info(token_data, self.SCOPES)
                else:
                    print(f"Invalid token data format: {type(token_data)}")
                    self.creds = None

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            elif self.use_oauth:
                client_secrets_file = os.getenv(f"GOOGLE_CLIENT_SECRETS_{self.account_id.upper()}")
                if not client_secrets_file:
                    raise ValueError(f"Client secrets file path not set for {self.account_id}")
                flow = Flow.from_client_secrets_file(client_secrets_file, self.SCOPES)
                flow.run_local_server(port=0)
                self.creds = flow.credentials
            else:
                raise ValueError("No valid credentials available. Please set up the config file or use OAuth.")

        if not self.use_oauth and self.config_path:
            with open(self.config_path, "w") as f:
                token_data = self.creds.to_json()
                json.dump({"token": token_data}, f)

        request = google.auth.transport.requests.Request()
        self.sheets_service = build("sheets", "v4", credentials=self.creds, requestBuilder=request)
        self.drive_service = build("drive", "v3", credentials=self.creds, requestBuilder=request)

    def create_spreadsheet(self, title: str, folder_id: str) -> Optional[str]:
        """
        Create a new spreadsheet and move it to the specified folder.

        Args:
            title (str): The title of the new spreadsheet.
            folder_id (str): The ID of the folder where the spreadsheet should be moved.

        Returns:
            str: The ID of the created spreadsheet, or None if an error occurred.
        """
        try:
            spreadsheet = (
                self.sheets_service.spreadsheets()
                .create(body={"properties": {"title": title}})
                .execute()
            )
            spreadsheet_id = spreadsheet["spreadsheetId"]

            # Move the spreadsheet to the specified folder
            file = (
                self.drive_service.files()
                .get(fileId=spreadsheet_id, fields="parents")
                .execute()
            )
            previous_parents = ",".join(file.get("parents", []))
            self.drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, parents",
            ).execute()

            return spreadsheet_id
        except HttpError as error:
            print(f"An error occurred while creating spreadsheet: {error}")
            return None

    def read_spreadsheet(
        self, spreadsheet_id: str, range_name: str
    ) -> Optional[List[List[Any]]]:
        try:
            result = (
                self.sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            return result.get("values", [])
        except HttpError as error:
            if error.resp.status == 403:
                print(
                    f"Permission denied: Make sure the service account has access to the spreadsheet."
                )
            else:
                print(f"An error occurred while reading spreadsheet: {error}")
            return None

    def write_to_spreadsheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        insert_data_option: str = "OVERWRITE",
    ) -> Optional[Dict[str, Any]]:
        try:
            body = {"values": values}
            result = (
                self.sheets_service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    insertDataOption=insert_data_option,
                    body=body,
                )
                .execute()
            )
            return result
        except HttpError as error:
            print(f"An error occurred while writing to spreadsheet: {error}")
            return None

    def get_folder_id(
        self, folder_name: str, parent_folder_id: str = "root"
    ) -> Optional[str]:
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            if parent_folder_id != "root":
                query += f" and '{parent_folder_id}' in parents"
            
            results = self.drive_service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                pageSize=1
            ).execute()
            
            items = results.get("files", [])
            if items:
                logger.info(f"Found folder '{folder_name}' with ID: {items[0]['id']}")
                return items[0]["id"]
            else:
                logger.warning(f"Folder '{folder_name}' not found")
                return None
        except HttpError as error:
            logger.error(f"An error occurred while getting folder ID: {error}")
            return None

    def read_range(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        # Implementation
        pass

    def write_range(
        self, spreadsheet_id: str, range_name: str, values: List[List[Any]]
    ) -> None:
        # Implementation
        pass

    def append_row(
        self, spreadsheet_id: str, sheet_name: str, values: List[Any]
    ) -> None:
        # Implementation
        pass

    def get_current_datetime(self) -> str:
        """Get the current date and time as a formatted string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_spreadsheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
    ) -> Optional[Dict[str, Any]]:
        try:
            body = {"values": values}
            result = (
                self.sheets_service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )
            return result
        except HttpError as error:
            print(f"An error occurred while updating spreadsheet: {error}")
            return None

    def append_to_spreadsheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
    ) -> Optional[Dict[str, Any]]:
        try:
            body = {"values": values}
            result = (
                self.sheets_service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )
            print(f"Append result: {result}")  # Add this line for debugging
            return result
        except HttpError as error:
            print(f"An error occurred while appending to spreadsheet: {error}")
            return None

    def batch_update(self, spreadsheet_id: str, updates: List[Dict[str, Any]]) -> None:
        """
        Perform a batch update on the spreadsheet.

        Args:
            spreadsheet_id (str): The ID of the spreadsheet to update.
            updates (List[Dict[str, Any]]): A list of update operations to perform.

        Raises:
            HttpError: If an error occurs during the API call.
        """
        try:
            body = {
                'valueInputOption': 'USER_ENTERED',
                'data': updates
            }
            self.sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            logger.info(f"Batch update completed successfully for {len(updates)} operations.")
        except HttpError as error:
            logger.error(f"An error occurred during batch update: {error}")
            raise

    def find_file_id(self, folder_id: str, file_name: str) -> Optional[str]:
        """
        Find the ID of a file in a specific folder.

        Args:
            folder_id (str): The ID of the folder to search in.
            file_name (str): The name of the file to find.

        Returns:
            Optional[str]: The ID of the file if found, None otherwise.

        Raises:
            HttpError: If an error occurs during the API call.
        """
        try:
            query = f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()
            files = results.get('files', [])
            if files:
                return files[0]['id']
            else:
                logger.warning(f"File '{file_name}' not found in folder '{folder_id}'")
                return None
        except HttpError as error:
            logger.error(f"An error occurred while searching for file '{file_name}': {error}")
            raise
