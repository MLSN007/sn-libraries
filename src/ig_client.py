"""
ig_client.py:
Manages the connection to Instagram using Instagrapi, loading the saved session for easy interaction.
"""
import os
import logging
from typing import Optional, Union
from instagrapi import Client
from instagrapi.exceptions import ClientLoginRequired, ClientError
from instagrapi.types import StoryHashtag, StoryLink, StoryMention, StorySticker 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IgClient:
    """
    A class to manage Instagram client operations using a saved session.
    """
    
    def __init__(self, session_file: str = "cl_ig.pkl") -> None:
        """
        Initialize the IgClient instance.

        Args:
            session_file (str): The filename of the saved session. Default is "cl_ig.pkl".

        Raises:
            FileNotFoundError: If the session file does not exist.
            ClientError: If there's an error loading the session file.
        """
        self.client = Client()
        self.session_file = session_file

        if not os.path.exists(session_file):
            raise FileNotFoundError("Session file not found. Please authenticate first.")

        try:
            self.client.load_settings(session_file)
            logger.info("Session loaded successfully.")
        except ClientError as e: 
            logger.error(f"An error occurred loading the session file: {e}")
            raise

    def get_user_id(self, username: str) -> Optional[int]:
        """
        Fetch the user ID for a given Instagram username.

        Args:
            username (str): The Instagram username to fetch the user ID for.

        Returns:
            Optional[int]: The user's ID (primary key) if found, None otherwise.

        Raises:
            UserNotFound: If the specified username does not exist.
            ClientError: For other Instagram client-related errors.
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
        Authenticates with Instagram and saves the session.

        Args:
            username (str, optional): The Instagram username. If not provided, 
                                      it will be retrieved from the environment variable 'IG_JK_user'.
            password (str, optional): The Instagram password. If not provided, 
                                      it will be retrieved from the environment variable 'IG_JK_psw'.

        Raises:
            ValueError: If username and/or password are not provided and cannot be retrieved 
                        from environment variables.
            ClientLoginRequired: If login fails due to invalid credentials.
            ClientError: For other Instagram client-related errors.
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