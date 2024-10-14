import os
import json
from typing import Optional, List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account


class GoogleSheetsHandler:
    """
    Handles interactions with Google Sheets and Drive APIs for multiple accounts.

    This class supports two modes of operation:
    1. Development mode: Uses local configuration files for credentials.
    2. Production mode: Uses the full OAuth 2.0 flow for desktop applications.

    Usage:
    - For development: handler = GoogleSheetsHandler('account1')
    - For production: handler = GoogleSheetsHandler('account1', use_oauth=True)
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
        self.creds = None
        self.sheets_service = None
        self.drive_service = None

    def _get_config_path(self) -> Optional[str]:
        """Get the configuration file path from environment variables."""
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
        if not self.use_oauth and os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                config = json.load(f)
            if "token" in config:
                token_data = config["token"]
                if isinstance(token_data, str):
                    token_data = json.loads(token_data)
                if isinstance(token_data, dict):
                    self.creds = Credentials.from_authorized_user_info(
                        token_data, self.SCOPES
                    )
                else:
                    print(f"Invalid token data format: {type(token_data)}")
                    self.creds = None

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    self.creds = None

            if not self.creds:
                client_secrets_file = os.getenv(
                    f"GOOGLE_CLIENT_SECRETS_{self.account_id.upper()}"
                )
                if not client_secrets_file:
                    raise ValueError(
                        f"Client secrets file path not set for {self.account_id}"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            if not self.use_oauth and self.config_path:
                with open(self.config_path, "w") as f:
                    token_data = json.dumps(json.loads(self.creds.to_json()))
                    json.dump({"token": token_data}, f)

        self.sheets_service = build("sheets", "v4", credentials=self.creds)
        self.drive_service = build("drive", "v3", credentials=self.creds)

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
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_folder_id}' in parents"
            results = (
                self.drive_service.files()
                .list(q=query, spaces="drive", fields="files(id, name)")
                .execute()
            )
            items = results.get("files", [])
            return items[0]["id"] if items else None
        except HttpError as error:
            print(f"An error occurred while getting folder ID: {error}")
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
