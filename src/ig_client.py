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
        Initialize the IgClient instance.

        Args:
            account_id (str): The ID of the Instagram account.

        Raises:
            FileNotFoundError: If the session file does not exist.
            ClientError: If there's an error loading the session file.
        """
        self.account_id = account_id
        self.config = IgConfig(account_id)
        self.client = Client()
        self.session_file = self._get_session_file_path()

        if os.path.exists(self.session_file):
            self.load_session()
        else:
            self.login()

    def _get_session_file_path(self) -> str:
        config_file_path = r"C:\Users\manue\Documents\GitHub007\sn-libraries\sessions"
        return str(Path(f"{config_file_path}/{self.account_id}_session.json").resolve())

    def load_session(self):
        """Load existing session and verify it's still valid."""
        self.client.load_settings(self.session_file)
        if not self.config.username or not self.config.password:
            raise ValueError("Username or password not set in the config file")
        self.client.login(self.config.username, self.config.password)

    def login(self):
        """Perform a fresh login and save the session."""
        if not self.config.username or not self.config.password:
            raise ValueError("Username or password not set in the config file")
        self.client.login(self.config.username, self.config.password)
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
            
            self.client = Client()  # Create new client instance
            self.login()  # Perform fresh login
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
