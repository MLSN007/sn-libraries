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
from instagrapi.exceptions import ClientLoginRequired, ClientError
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
        return str(Path(f"sessions/{self.account_id}_session.json").resolve())

    def load_session(self):
        self.client.load_settings(self.session_file)
        self.client.login(self.config.username, self.config.password)

    def login(self):
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

    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> None:
        """
        Logs into Instagram with the provided credentials and saves the session.

        If username or password are not provided, they are retrieved from the environment variables 
        IG_JK_user and IG_JK_psw, respectively.

        Args:
            username (str, optional): Your Instagram username.
            password (str, optional): Your Instagram password.

        Raises:
            ValueError: If username and/or password are not provided and are not set in environment variables.
            ClientLoginRequired: If the login fails (e.g., due to invalid credentials).
            ClientError: For other Instagrapi-related errors.
        """

        if not username:
            username = os.environ.get("IG_JK_user")
        if not password:
            password = os.environ.get("IG_JK_psw")

        if not username or not password:
            raise ValueError(
                "Username and password must be provided or set as environment variables."
            )

        try:
            self.client.login(username, password)
            logger.info("Connected Successfully!")
            self.client.dump_settings(self.session_file)  # Save the session
        except ClientLoginRequired:
            logger.error("Login failed. Please check your credentials.")
            raise
        except ClientError as e:
            logger.error(f"An error occurred during login: {e}")
            raise
