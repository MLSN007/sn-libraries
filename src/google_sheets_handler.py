import json
import logging
import os
import pytz
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from googleapiclient._apis.sheets.v4.resources import SpreadsheetsResource
    from googleapiclient._apis.drive.v3.resources import FilesResource, DriveResource, AboutResource

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build, Resource
import google.auth.transport.requests

logging.basicConfig(level=logging.DEBUG)  # Change level to DEBUG
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
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/documents",
    ]

    def __init__(self, account_id: str, spreadsheet_id: Optional[str] = None):
        """
        Initialize the GoogleSheetsHandler.

        Args:
            account_id (str): Identifier for the Google account to use.
            spreadsheet_id (Optional[str]): The ID of the spreadsheet to use.
        """

        self.account_id = account_id
        self.spreadsheet_id = spreadsheet_id
        self.use_oauth = False
        self.config_path = self._get_config_path()
        self.creds: Optional[Credentials] = None
        self.sheets_service: Optional[Resource] = None
        self.drive_service: Optional[Resource] = None

    def _get_config_path(self) -> Optional[str]:
        """Get the configuration file path from environment variables."""
        # Convert account_id to upper case to ensure consistency in environment variable names

        env_var = f"GOOGLE_SHEETS_CONFIG_{self.account_id.upper()}"
        config_path = os.getenv(env_var)
        if not self.use_oauth and not config_path:
            raise ValueError(f"Environment variable {env_var} is not set")
        return config_path

    def authenticate(self) -> None:
        """Authenticate with Google APIs."""
        try:
            config_path = self._get_config_path()

            if not self.use_oauth and config_path and os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    if "token" in config:
                        token_data = config["token"]
                        if isinstance(token_data, str):
                            token_data = json.loads(token_data)
                            self.creds = Credentials.from_authorized_user_info(
                                token_data, self.SCOPES
                            )

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                    except RefreshError:
                        logger.error("Token refresh failed, need to re-authenticate")
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

            print(f"Token expiry time: {self.creds.expiry}")

            # Save the credentials
            if not self.use_oauth and config_path:
                with open(config_path, "w") as f:
                    token_data = self.creds.to_json()
                    json.dump({"token": token_data}, f)

            # Build services with static HTTP
            self.sheets_service = cast(Resource, build("sheets", "v4", credentials=self.creds))
            self.drive_service = cast(Resource, build("drive", "v3", credentials=self.creds))

            logger.info("Successfully authenticated with Google services")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self.sheets_service = None
            self.drive_service = None
            raise

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
            print(f"Reading spreadsheet {spreadsheet_id} with range {range_name}")
            result = (
                self.sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            return result.get("values", [])
        except RefreshError as e:
            print(f"Error refreshing token: {e}")
            # Handle the error (e.g., log the error, retry with exponential backoff)

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

    def get_folder_id(self, folder_name: str) -> Optional[str]:
        try:
            # First, let's list all folders in the root of My Drive
            query = "mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false"
            logger.debug(f"Executing Drive API query for all folders: {query}")
            results = (
                self.drive_service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name)",
                    pageSize=100,  # Adjust this if you have more folders
                )
                .execute()
            )
            logger.debug(f"All folders in root: {results}")

            # Now, let's search for our specific folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and 'root' in parents and trashed=false"
            logger.debug(f"Executing Drive API query for specific folder: {query}")
            results = (
                self.drive_service.files()
                .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
                .execute()
            )
            logger.debug(f"Drive API response for specific folder: {results}")

            items = results.get("files", [])
            if not items:
                logger.warning(f"Folder '{folder_name}' not found")
                return None
            return items[0]["id"]
        except Exception as e:
            logger.error(f"Error while getting folder ID: {str(e)}")
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

    def batch_update(self, spreadsheet_id: str, data: List[Dict[str, Any]]) -> bool:
        """
        Perform a batch update on the spreadsheet.

        Args:
            spreadsheet_id (str): The ID of the spreadsheet to update
            data (List[Dict[str, Any]]): List of update operations, each containing 'range' and 'values'

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": item["range"], "values": item["values"]} for item in data
                ],
            }

            result = (
                self.sheets_service.spreadsheets()
                .values()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )

            logger.info(
                f"Batch update successful: {result.get('totalUpdatedCells')} cells updated"
            )
            return True

        except Exception as e:
            logger.error(f"Error performing batch update: {e}")
            return False

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
            query = (
                f"'{folder_id}' in parents and name = '{file_name}' and trashed = false"
            )
            results = (
                self.drive_service.files()
                .list(q=query, spaces="drive", fields="files(id, name)", pageSize=1)
                .execute()
            )
            files = results.get("files", [])
            if files:
                return files[0]["id"]
            else:
                logger.warning(f"File '{file_name}' not found in folder '{folder_id}'")
                return None
        except HttpError as error:
            logger.error(
                f"An error occurred while searching for file '{file_name}': {error}"
            )
            raise

    def get_user_email(self):
        """Returns the email address of the authenticated user."""
        try:
            # Assuming self.creds is an instance of google.oauth2.credentials.Credentials
            user_info = self.creds.id_token
            print(f"User info: {user_info}")
            print(type(user_info))
            if user_info and isinstance(
                user_info, dict
            ):  # Check if user_info is a dictionary
                return user_info.get("email")
            else:
                print(
                    "Error: Could not retrieve user email. User info is not in the expected format."
                )
                return None
        except AttributeError:
            print(
                "Error: Could not retrieve user email. Credentials might be missing or invalid."
            )
            return None

    def check_permissions(self):
        try:
            about = self.drive_service.about().get(fields="user,storageQuota").execute()
            logger.debug(f"User info: {about['user']}")
            logger.debug(f"Storage quota: {about['storageQuota']}")

            # Try to list drives, but don't fail if user doesn't have access
            try:
                drives = self.drive_service.drives().list().execute()
                logger.debug(f"Accessible drives: {drives}")
            except HttpError as e:
                if e.resp.status == 403:
                    logger.warning(
                        "User doesn't have access to shared drives. This is not critical."
                    )
                else:
                    raise

            return True
        except Exception as e:
            logger.error(f"Error checking permissions: {str(e)}")
            return False

    def get_rows_without_content_id(self) -> list:
        """
        Fetches rows from the Google Sheet that do not have a content_id and have data in 'consecutive_input_#'.

        Returns:
            list: A list of dictionaries representing rows without content_id.
        """
        try:
            # Read the spreadsheet data
            data = self.read_spreadsheet(self.spreadsheet_id, "A:S")
            if not data:
                logger.error("Failed to read spreadsheet data")
                return []

            header = data[0]
            content_id_index = header.index("content_id")
            consecutive_input_index = header.index("consecutive_input_#")

            rows_without_content_id = []
            for row_idx, row in enumerate(
                data[1:], start=2
            ):  # Start from 2 to account for header row
                if len(row) <= max(content_id_index, consecutive_input_index):
                    logger.warning(f"Row {row_idx} is missing expected columns: {row}")
                    continue
                if row[consecutive_input_index].isdigit() and not row[content_id_index]:
                    row_dict = {
                        header[i]: row[i] if i < len(row) else None
                        for i in range(len(header))
                    }
                    row_dict["row_index"] = (
                        row_idx  # Add the actual row number from Google Sheet
                    )
                    rows_without_content_id.append(row_dict)

            return rows_without_content_id
        except Exception as e:
            logger.error(f"Error fetching rows without content_id: {e}")
            return []

    def update_content_ids(self, rows: list, content_ids: list) -> None:
        """
        Updates the Google Sheet with the provided content_ids in the correct column.

        Args:
            rows (list): A list of dictionaries representing rows to update.
            content_ids (list): A list of content_ids to write back to the Google Sheet.
        """
        try:
            # First, get the header row to find the content_id column
            header_range = "'Ig Origin Data'!1:1"
            headers = self.read_spreadsheet(self.spreadsheet_id, header_range)

            if not headers or not headers[0]:
                logger.error("Failed to read Google Sheet headers")
                return

            # Find the content_id column index
            try:
                content_id_col_idx = headers[0].index("content_id")
                # Convert to column letter (0-based index to A1 notation)
                content_id_col = self._number_to_column_letter(content_id_col_idx + 1)
            except ValueError:
                logger.error("Could not find 'content_id' column in sheet headers")
                return

            updates = []
            for row, content_id in zip(rows, content_ids):
                row_index = row["row_index"]
                updates.append(
                    {
                        "range": f"'Ig Origin Data'!{content_id_col}{row_index}",
                        "values": [[content_id]],
                    }
                )

            if updates:
                self.batch_update(self.spreadsheet_id, updates)
                logger.info(
                    "Updated %s content IDs in column %s", len(updates), content_id_col
                )
        except Exception as e:
            logger.error("Error updating content IDs: %s", str(e))

    def _number_to_column_letter(self, n: int) -> str:
        """
        Convert a column number to Excel-style column letter (A, B, C, ... Z, AA, AB, etc.)
        
        Args:
            n (int): The column number (1-based)
            
        Returns:
            str: The Excel-style column letter
        """
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string

    def batch_update_values(self, data: List[Dict]) -> None:
        """
        Perform a batch update of values in the spreadsheet
        
        Args:
            data (List[Dict]): List of dictionaries containing range and values to update
        """
        try:
            body = {
                'valueInputOption': 'RAW',
                'data': data
            }
            self.sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
        except Exception as e:
            logger.error('Error performing batch update: %s', e)
            raise
