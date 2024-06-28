"""
ig_auth.py:
Handles initial authentication with Instagram to create a session file for future interactions.
NEVER commit the session file to version control (add it to your .gitignore).
"""
import os
import logging
from typing import Optional
from instagrapi import Client
from instagrapi.exceptions import ClientLoginRequired, ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def authenticate_and_save_session(session_file: str = "cl_ig.pkl") -> None:
    """
    Authenticates with Instagram using system environment variables for credentials
    and saves the session to a file.

    Args:
        session_file (str): The filename to save the session. Default is "cl_ig.pkl".

    Raises:
        ValueError: If USERNAME and PASSWORD environment variables are not set.
        ClientLoginRequired: If login fails due to invalid credentials.
        ClientError: For other Instagram client-related errors.
    """
    username: Optional[str] = os.environ.get("IG_JK_user")
    password: Optional[str] = os.environ.get("IG_JK_psw")

    if not username or not password:
        raise ValueError("USERNAME and PASSWORD must be set as system environment variables.")

    cl = Client()
    try:
        cl.login(username, password)
        logger.info("Connected Successfully!")
        cl.dump_settings(session_file)
    except ClientLoginRequired:
        logger.error("Login failed. Please check your credentials.")
        raise
    except ClientError as e:
        logger.error(f"An error occurred during login: {e}")
        raise