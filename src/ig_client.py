"""
    This module manages the connection to Instagram using Instagrapi. It provides a class,
IgClient, which handles loading saved sessions, user ID retrieval, and logging into 
Instagram. The module uses environment variables for storing credentials and leverages 
logging for better feedback.
"""

import os
import logging
from typing import Optional, Union
from instagrapi import Client
from instagrapi.exceptions import ClientLoginRequired, ClientError, UserNotFound
from instagrapi.types import StoryHashtag, StoryLink, StoryMention, StorySticker
from pathlib import Path
from ig_config import IgConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IgClient:
    """
    A class to manage Instagram client operations using a saved session.

    Attributes:
        client (instagrapi.Client): The Instagrapi Client object for interacting with Instagram.
        session_file (str): The filename of the saved session file.

    Raises:
        FileNotFoundError: If the specified session file does not exist.
        ClientError: If there's an error loading the session file.
    """

    def __init__(self, account_id: str):
        """
        Initialize Instagram client with account credentials.

        Args:
            account_id (str): The Instagram account identifier
        """
        self.account_id = account_id
        self.session_file = f"sessions/{account_id}_session.json"

        # Load config
        self.config = IgConfig(account_id)

        # Set device settings
        self.device_settings = {
            "app_version": "269.0.0.18.75",
            "android_version": 26,
            "android_release": "8.0.0",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "SAMSUNG",
            "device": "SM-G950F",
            "model": "G950F",
            "cpu": "universal8895",
            "version_code": "314665256",
        }

        # Initialize client
        self.client = Client()
        self.client.set_device(self.device_settings)

        # Load existing session if available
        if os.path.exists(self.session_file):
            self.client.load_settings(self.session_file)

    def _get_session_file_path(self) -> str:
        config_file_path = r"C:\Users\manue\Documents\GitHub007\sn-libraries\sessions"
        return str(Path(f"{config_file_path}/{self.account_id}_session.json").resolve())

    def load_session(self):
        """Load existing session and verify it's still valid."""
        self.client.load_settings(self.session_file)
        if not self.credentials.username or not self.credentials.password:
            raise ValueError("Username or password not set in the config file")
        self.client.login(self.credentials.username, self.credentials.password)

    def login(self):
        """Perform a fresh login and save the session."""
        if not self.credentials.username or not self.credentials.password:
            raise ValueError("Username or password not set in the config file")

        # Initialize client with device settings
        self.client = Client()
        self.client.set_device(self.device_settings)  # Set device settings before login

        self.client.login(self.credentials.username, self.credentials.password)
        self.save_session()

    def save_session(self):
        self.client.dump_settings(self.session_file)

    def get_user_id(self, username: str) -> Optional[int]:
        """
        Fetches the user ID (pk) for a given Instagram username.

        Args:
            username (str): The Instagram username.

        Returns:
            Optional[int]: The user's ID if found, None if not found.

        Raises:
            UserNotFound: If the username doesn't exist.
            ClientError: For other Instagrapi-related errors.
        """
        try:
            user_info = self.client.user_info_by_username(username)
            logger.info(f"Successfully fetched user ID for {username}")
            return user_info.pk
        except UserNotFound:
            logger.warning(f"User not found: {username}")
            return None
        except ClientError as e:
            logger.error(f"An error occurred fetching user ID for {username}: {e}")
            raise

    def reset_session(self) -> bool:
        """
        Reset the session by removing existing session file and performing a fresh login.
        
        Returns:
            bool: True if reset and login successful, False otherwise
        """
        try:
            logger.info("Resetting Instagram session...")
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.info("Removed existing session file")
            
            # Initialize client with device settings
            self.client = Client()
            self.client.set_device(self.device_settings)
            
            # Get credentials from config
            credentials = self.config.get_credentials()
            username = credentials.get("username")
            password = credentials.get("password")
            
            if not username or not password:
                raise ValueError("Username or password not found in config")
            
            # Perform fresh login
            self.client.login(username, password)
            self.save_session()
            
            logger.info("Successfully reset session and performed fresh login")
            return True
        except Exception as e:
            logger.error(f"Failed to reset session: {e}")
            return False

    def validate_session(self) -> bool:
        """Validate the current session and relogin if necessary."""
        try:
            logger.info("Validating Instagram session...")
            self.client.account_info()
            logger.info("✅ Session is valid")
            return True
        except Exception as e:
            logger.warning(f"❌ Session validation failed: {e}")
            try:
                logger.info("Attempting to reset session and perform fresh login...")
                if self.reset_session():
                    # Verify the new session
                    self.client.account_info()
                    logger.info("✅ New session is valid")
                    return True
                else:
                    logger.error("❌ Session reset failed")
                    return False
            except Exception as e:
                logger.error(f"❌ Login failed after session reset: {e}")
                return False

    def _load_or_create_session(self) -> None:
        """Load existing session or create new one if it doesn't exist."""
        try:
            if os.path.exists(self.session_file):
                logger.info(f"Loading existing session from {self.session_file}")
                self.load_session()
            else:
                logger.info("No existing session found, performing fresh login")
                self.login()

            # Verify the session is valid
            self.client.account_info()
            logger.info("Session loaded and verified successfully")

        except Exception as e:
            logger.warning(f"Error loading session: {e}")
            logger.info("Attempting fresh login...")
            try:
                self.login()
                logger.info("Fresh login successful")
            except Exception as login_error:
                logger.error(f"Login failed: {login_error}")
                raise
