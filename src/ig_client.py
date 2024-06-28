"""
ig_client.py:
Manages the connection to Instagram using Instagrapi, loading the saved session for easy interaction.
"""
import os
import logging
from typing import Optional
from instagrapi import Client
from instagrapi.exceptions import ClientError, UserNotFound
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
