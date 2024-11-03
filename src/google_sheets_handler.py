"""
Handles interactions with Google Sheets API for Instagram content management.

This module provides a handler class for interacting with Google Sheets and Drive APIs,
implementing OAuth2 authentication, caching, connection pooling, and resource management.

Classes:
    GoogleSheetsHandler: Main handler class for Google Sheets operations.
    MemoryCache: Cache implementation for Google API discovery.

Typical usage:
    handler = GoogleSheetsHandler(account_id="JK")
    if handler.authenticate():
        handler.get_folder_id("my_folder")
"""

# Standard library imports
import json
import logging
import os
import socket
import ssl
import traceback
import warnings
from contextlib import contextmanager, ExitStack
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from typing import Any, ClassVar, Dict, List, Optional, Union

# Third-party imports
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.discovery_cache.base import Cache
from googleapiclient.errors import HttpError
from urllib3 import PoolManager

# Local imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from google_api_types import DriveService, SheetsService, UserinfoService

# Configure logging
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings(
    "ignore", message="file_cache is only supported with oauth2client<4.0.0"
)

logger = logging.getLogger(__name__)


class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


def timed_lru_cache(seconds: int, maxsize: int = 128):
    """Decorator that creates a time-based LRU cache."""

    def decorator(func):
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = datetime.now()

            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < timedelta(seconds=seconds):
                    return result
                else:
                    del cache[key]

            result = func(*args, **kwargs)
            cache[key] = (result, now)

            # Implement LRU by removing oldest entries if cache is too large
            if len(cache) > maxsize:
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]

            return result

        return wrapper

    return decorator


class GoogleSheetsHandler:
    """Handles Google Sheets operations for Instagram content."""

    _authenticated: bool = False

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",  # Read/write spreadsheets
        "https://www.googleapis.com/auth/drive",  # Full Drive access
        "https://www.googleapis.com/auth/drive.file",  # Access to files created/opened by app
        "https://www.googleapis.com/auth/drive.readonly",  # Read all files
        "https://www.googleapis.com/auth/documents",  # Access to Google Docs
        "https://www.googleapis.com/auth/userinfo.profile",  # Get user profile info
        "https://www.googleapis.com/auth/userinfo.email",  # Get user email
        "openid",  # Add this scope to match OAuth2 flow
    ]

    # Class-level connection pool
    _connection_pool: ClassVar[Optional[PoolManager]] = None
    _pool_size: ClassVar[int] = 10

    @classmethod
    def get_connection_pool(cls) -> PoolManager:
        """Get or create connection pool."""
        if cls._connection_pool is None:
            cls._connection_pool = PoolManager(
                maxsize=cls._pool_size, retries=3, timeout=30.0
            )
        return cls._connection_pool

    def __init__(self, account_id: str):
        """Initialize the Google Sheets handler."""
        self.account_id = account_id
        env_var_name = f"GOOGLE_SHEETS_CONFIG_{self.account_id}"
        self.config_path = os.getenv(env_var_name)
        if not self.config_path:
            raise ValueError(f"{env_var_name} environment variable not set")

        logger.info(f"Using config from {env_var_name}: {self.config_path}")

        self.creds: Optional[Credentials] = None
        self.sheets_service: Optional[SheetsService] = None
        self.drive_service: Optional[DriveService] = None
        self.spreadsheet_id: Optional[str] = None
        self.folder_id: Optional[str] = None

        # Suppress discovery cache warnings
        warnings.filterwarnings(
            "ignore", message="file_cache is only supported with oauth2client<4.0.0"
        )

        # Use memory cache instead of file cache
        self.cache = MemoryCache()

        self.pool = self.get_connection_pool()

        self._cache_timeout = 300  # 5 minutes
        self._batch_size = 100
        self._last_batch_request = None
        self._pending_updates = []

    def authenticate(self) -> bool:
        """
        Authenticate with Google Services using OAuth2 credentials.
        Handles token refresh and updates the config file when needed.
        """
        if self._authenticated:
            return True

        try:
            if not os.path.exists(self.config_path):
                raise ValueError(f"Config file not found at: {self.config_path}")

            # Load the OAuth2 credentials from the config file
            with open(self.config_path) as f:
                config_data = json.load(f)
                if "token" not in config_data:
                    raise ValueError("No token data found in config file")
                token_data = json.loads(config_data["token"])

            # Create credentials from the token data
            self.creds = Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=self.SCOPES,
            )

            # Check if credentials need refresh
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    logger.info("Token expired, refreshing credentials...")
                    self.creds.refresh(Request())
                    self._save_refreshed_credentials()
                    logger.info("Credentials refreshed and saved")
                else:
                    logger.warning("Need to rerun initial setup to get new credentials")
                    return False

            # Verify credentials by getting user info
            userinfo_service: UserinfoService = build("oauth2", "v2", credentials=self.creds)  # type: ignore[no-untyped-call]
            user_info = userinfo_service.userinfo().get().execute()  # type: ignore[attr-defined]

            logger.info(f"Authenticated as: {user_info.get('email')}")

            # Build services with proper type hints
            self.sheets_service = build("sheets", "v4", credentials=self.creds)  # type: ignore[no-untyped-call]
            self.drive_service = build("drive", "v3", credentials=self.creds)  # type: ignore[no-untyped-call]

            logger.info("Successfully authenticated with Google services")
            self._authenticated = True
            return True

        except RefreshError as e:
            logger.error("Token refresh failed: %s", str(e))
            logger.error("Please re-run initial_setup.py to get new credentials")
            return False
        except ValueError as e:
            logger.error("Authentication failed: %s", str(e))
            return False
        except Exception as e:
            logger.error("Unexpected authentication error: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            return False

    def _save_refreshed_credentials(self) -> None:
        """Save refreshed credentials back to the config file."""
        try:
            if not self.creds:
                raise ValueError("No credentials to save")

            # Create token data
            token_data = {
                "token": self.creds.token,
                "refresh_token": self.creds.refresh_token,
                "token_uri": self.creds.token_uri,
                "client_id": self.creds.client_id,
                "client_secret": self.creds.client_secret,
                "scopes": self.creds.scopes,
                "expiry": self.creds.expiry.isoformat() if self.creds.expiry else None,
            }

            # Read existing config
            with open(self.config_path) as f:
                config_data = json.load(f)

            # Update token
            config_data["token"] = json.dumps(token_data)

            # Write updated config back to file
            with open(self.config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info("Updated credentials saved to config file")

        except Exception as e:
            logger.error("Failed to save refreshed credentials: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise

    def _handle_api_error(self, error: Exception, context: str) -> None:
        """
        Handle API errors with appropriate logging and actions.

        Args:
            error (Exception): The error that occurred
            context (str): Description of what was being attempted
        """
        if isinstance(error, HttpError):
            if error.resp.status == 401:
                logger.error("Authentication error: %s", str(error))
                if self.creds and self.creds.expired:
                    logger.info("Attempting to refresh credentials...")
                    try:
                        self.creds.refresh(Request())
                        self._save_refreshed_credentials()
                        logger.info("Successfully refreshed credentials")
                    except Exception as refresh_error:
                        logger.error(
                            "Failed to refresh credentials: %s", str(refresh_error)
                        )
            elif error.resp.status == 403:
                logger.error("Permission denied: %s", str(error))
                logger.error("Please check the permissions for this resource")
            elif error.resp.status == 404:
                logger.error("Resource not found: %s", str(error))
            else:
                logger.error("API error (%d): %s", error.resp.status, str(error))
        else:
            logger.error("Error during %s: %s", context, str(error))
            logger.error("Traceback: %s", traceback.format_exc())

    def initialize_spreadsheet(self, spreadsheet_id: str) -> bool:
        """
        Initialize the spreadsheet for operations.

        Args:
            spreadsheet_id (str): The ID of the Google Sheet

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.spreadsheet_id = spreadsheet_id
            # Test access by getting spreadsheet metadata
            self.sheets_service.spreadsheets().get(  # type: ignore
                spreadsheetId=self.spreadsheet_id
            ).execute()

            logger.info("Successfully initialized spreadsheet: %s", spreadsheet_id)
            return True

        except HttpError as e:
            logger.error("Failed to initialize spreadsheet: %s", str(e))
            return False

    @contextmanager
    def _managed_ssl_connection(self):
        """Context manager for handling SSL connections with proper cleanup."""
        with ExitStack() as stack:
            old_socket = socket.socket
            old_ssl_context = ssl.create_default_context

            try:
                # Create a list to track all opened sockets
                opened_sockets = []

                def track_socket(*args, **kwargs):
                    sock = old_socket(*args, **kwargs)
                    opened_sockets.append(sock)
                    return sock

                # Override socket creation to track all sockets
                socket.socket = track_socket
                yield

            finally:
                # Restore original socket
                socket.socket = old_socket
                ssl.create_default_context = old_ssl_context

                # Close all tracked sockets
                for sock in opened_sockets:
                    try:
                        sock.close()
                    except Exception:
                        pass

    def get_folder_id(self, folder_name: str) -> Optional[str]:
        """
        Get the Google Drive folder ID by name.

        Args:
            folder_name (str): Name of the folder to find

        Returns:
            Optional[str]: Folder ID if found, None otherwise
        """
        with self._managed_ssl_connection():
            try:
                # First, let's see what permissions we have
                logger.info("Checking user permissions...")
                # Get user info from credentials
                try:
                    userinfo_service = build("oauth2", "v2", credentials=self.creds)
                    user_info = userinfo_service.userinfo().get().execute()
                    user_email = user_info.get("email", "Unknown")
                except Exception as e:
                    logger.warning(f"Could not get user info: {e}")
                    user_email = "Unknown"

                logger.info(f"Authenticated as: {user_email}")

                # List all accessible files and folders
                logger.info("Listing ALL accessible files and folders:")
                results = (
                    self.drive_service.files()
                    .list(  # type: ignore
                        q="",  # Empty query to get everything
                        spaces="drive",
                        fields="files(id, name, mimeType, parents, owners, permissions)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                    )
                    .execute()
                )

                items = results.get("files", [])
                logger.info(f"Total accessible items: {len(items)}")

                # Log details of each item
                for item in items:
                    item_type = (
                        "📁 "
                        if item.get("mimeType") == "application/vnd.google-apps.folder"
                        else "📄 "
                    )
                    owner = (
                        item.get("owners", [{}])[0].get("emailAddress", "Unknown")
                        if "owners" in item
                        else "Unknown"
                    )
                    logger.info(
                        f"{item_type}{item['name']} (ID: {item['id']}) - Owner: {owner}"
                    )

                # Now try to find our specific folder
                logger.info(f"\nSearching for folder: {folder_name}")
                folder_query = (
                    f"name='{folder_name}' and "
                    f"mimeType='application/vnd.google-apps.folder' and "
                    f"trashed=false"
                )

                logger.info("Executing folder query: %s", folder_query)
                folder_results = (
                    self.drive_service.files()
                    .list(  # type: ignore
                        q=folder_query,
                        spaces="drive",
                        fields="files(id, name, parents, permissions)",
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                    )
                    .execute()
                )

                folders = folder_results.get("files", [])

                if folders:
                    for folder in folders:
                        logger.info("Found matching folder:")
                        logger.info("  Name: %s", folder.get("name"))
                        logger.info("  ID: %s", folder.get("id"))
                        logger.info("  Permissions: %s", folder.get("permissions", []))
                else:
                    logger.error("No folders found matching query")

                if not folders:
                    logger.error(f"Folder '{folder_name}' not found. Please check:")
                    logger.error(
                        "1. The folder exists and name is exact (case-sensitive)"
                    )
                    logger.error(f"2. User {user_email} has access")
                    logger.error("3. The folder has been shared with your account")
                    return None

                folder_id = folders[0]["id"]
                logger.info(f"Found folder '{folder_name}' with ID: {folder_id}")
                return folder_id

            except Exception as e:
                logger.error(f"Error getting folder ID: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                return None

    def _get_folder_path(self, folder_id: str) -> List[str]:
        """Get the full path of a folder."""
        path = []
        current_id = folder_id

        while current_id:
            try:
                folder = (
                    self.drive_service.files()
                    .get(fileId=current_id, fields="name, parents")  # type: ignore
                    .execute()
                )

                path.insert(0, folder["name"])
                parents = folder.get("parents", [])
                current_id = parents[0] if parents else None

            except Exception:
                break

        return path

    def verify_file_access(self, file_id: str) -> bool:
        """
        Verify if a file exists and is accessible.

        Args:
            file_id (str): The Google Drive file ID

        Returns:
            bool: True if file is accessible, False otherwise
        """
        try:
            file = (
                self.drive_service.files()
                .get(fileId=file_id, fields="id, name, mimeType")
                .execute()
            )

            logger.info(
                "Successfully verified access to file: %s", file.get("name", file_id)
            )
            return True

        except Exception as e:
            logger.error("Error verifying file %s: %s", file_id, str(e))
            return False

    @lru_cache(maxsize=100)
    def get_file_id_by_name(
        self, file_name: str, folder_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get file ID by name, optionally within a specific folder. Results are cached.
        
        Args:
            file_name (str): Name of the file to find
            folder_id (Optional[str]): ID of the folder to search in, if None searches everywhere
            
        Returns:
            Optional[str]: File ID if found, None otherwise
        """
        try:
            # Build the query
            query_parts = [f"name = '{file_name}'", "trashed = false"]
            if folder_id:
                query_parts.append(f"parents in '{folder_id}'")
            
            query = " and ".join(query_parts)
            logger.debug(f"Searching for file with query: {query}")
            
            # Execute the search
            results = (
                self.drive_service.files()  # type: ignore[attr-defined]
                .list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, mimeType)',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                )
                .execute()
            )
            
            files = results.get('files', [])
            
            if not files:
                logger.warning(f"No file found with name: {file_name}")
                return None
                
            if len(files) > 1:
                logger.warning(f"Multiple files found with name: {file_name}. Using first match.")
                for file in files:
                    logger.debug(f"Found file: {file['name']} (ID: {file['id']})")
                
            file_id = files[0]['id']
            logger.info(f"Found file '{file_name}' with ID: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"Error getting file ID for '{file_name}': {str(e)}")
            return None

    def list_folder_contents(self, folder_id: str) -> List[Dict[str, str]]:
        """Optimized folder listing with pagination and caching."""

        @timed_lru_cache(seconds=300, maxsize=1)  # Cache for 5 minutes
        def _list_folder_contents_cached(folder_id: str) -> List[Dict[str, str]]:
            all_items = []
            page_token = None

            while True:
                try:
                    # Build query parameters
                    params = {
                        "q": f"'{folder_id}' in parents",
                        "spaces": "drive",
                        "fields": "nextPageToken, files(id, name, mimeType)",
                        "pageSize": 1000,
                    }
                    if page_token:
                        params["pageToken"] = page_token

                    results = self.drive_service.files().list(**params).execute()  # type: ignore

                    items = results.get("files", [])
                    all_items.extend(items)

                    # Get next page token
                    page_token = results.get("nextPageToken")
                    if not page_token:
                        break

                except Exception as e:
                    logger.error(f"Error listing folder contents: {e}")
                    break

            return all_items

        return _list_folder_contents_cached(folder_id)

    def verify_file_exists(self, file_id: str) -> bool:
        """Verify if a file exists in Google Drive."""
        return self.verify_file_access(file_id)

    def read_spreadsheet(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """
        Read data from a Google Sheet range.

        Args:
            spreadsheet_id (str): The ID of the spreadsheet
            range_name (str): The A1 notation of the range to read

        Returns:
            List[List[Any]]: The values from the spreadsheet
        """
        try:
            # Type ignore because sheets_service.spreadsheets() is dynamically created
            result = (
                self.sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)  # type: ignore
                .execute()
            )
            return result.get("values", [])
        except Exception as e:
            logger.error("Error reading spreadsheet: %s", str(e))
            return []

    def batch_update(self, spreadsheet_id: str, data: List[Dict[str, Any]]) -> bool:
        """Batched updates with automatic flushing."""
        self._pending_updates.extend(data)

        should_flush = (
            len(self._pending_updates) >= self._batch_size
            or self._last_batch_request is None
            or datetime.now() - self._last_batch_request
            > timedelta(seconds=self._cache_timeout)
        )

        if should_flush:
            return self._flush_updates(spreadsheet_id)
        return True

    def _flush_updates(self, spreadsheet_id: str) -> bool:
        """Flush pending updates to Google Sheets."""
        if not self._pending_updates:
            return True

        try:
            body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": item["range"], "values": item["values"]}
                    for item in self._pending_updates
                ],
            }

            self.sheets_service.spreadsheets().values().batchUpdate(  # type: ignore
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self._pending_updates = []
            self._last_batch_request = datetime.now()
            return True

        except Exception as e:
            logger.error(f"Failed to flush updates: {e}")
            return False

    def get_media(self, file_id: str) -> Optional[Any]:
        """Get media file from Google Drive."""
        try:
            # Type ignore because drive_service.files() is dynamically created
            request = self.drive_service.files().get_media(  # type: ignore
                fileId=file_id
            )
            return request
        except Exception as e:
            logger.error("Error getting media file: %s", str(e))
            return None

    def get(self, file_id: str, fields: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Google Drive."""
        try:
            # Type ignore because drive_service.files() is dynamically created
            return (
                self.drive_service.files()
                .get(fileId=file_id, fields=fields)  # type: ignore
                .execute()
            )
        except Exception as e:
            logger.error("Error getting file metadata: %s", str(e))
            return None

    def _make_request(self, method: str, url: str, **kwargs) -> Any:
        """Make HTTP request using connection pool with proper cleanup."""
        with self._managed_ssl_connection():
            try:
                response = self.pool.request(method, url, **kwargs)
                return response
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

    def cleanup(self) -> None:
        """Cleanup resources and flush pending updates."""
        try:
            # Flush any pending updates
            if self._pending_updates:
                self._flush_updates(self.spreadsheet_id)

            # Clear caches
            self.get_file_id_by_name.cache_clear()

            # Close connections
            if self._connection_pool:
                self._connection_pool.clear()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def check_permissions(self) -> bool:
        """
        Check if the authenticated user has necessary permissions.
        
        Returns:
            bool: True if user has required permissions, False otherwise
        """
        try:
            # Test drive access
            self.drive_service.about().get(fields="user").execute()  # type: ignore[attr-defined]
            
            # Test sheets access if spreadsheet_id is set
            if self.spreadsheet_id:
                self.sheets_service.spreadsheets().get(  # type: ignore[attr-defined]
                    spreadsheetId=self.spreadsheet_id
                ).execute()
            
            return True
            
        except HttpError as e:
            logger.error("Permission check failed: %s", str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error during permission check: %s", str(e))
            return False

    def batch_update_values(self, batch_data: List[Dict[str, Any]]) -> bool:
        """
        Update multiple cells in the spreadsheet in a single batch request.
        
        Args:
            batch_data (List[Dict[str, Any]]): List of update operations with range and values
                Each dict should have format: {"range": "Sheet1!A1", "values": [[value]]}
                
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            body = {
                "valueInputOption": "USER_ENTERED",
                "data": batch_data
            }
            
            self.sheets_service.spreadsheets().values().batchUpdate(  # type: ignore[attr-defined]
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            logger.info(f"Successfully batch updated {len(batch_data)} ranges")
            return True
            
        except Exception as e:
            logger.error(f"Error in batch update: {str(e)}")
            return False
