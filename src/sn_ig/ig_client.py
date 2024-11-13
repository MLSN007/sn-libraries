"""
    This module manages the connection to Instagram using Instagrapi. It provides a class,
IgClient, which handles loading saved sessions, user ID retrieval, and logging into 
Instagram. The module uses environment variables for storing credentials and leverages 
logging for better feedback.
"""

import os
import logging
from typing import Optional
from pathlib import Path
import time
import random
import requests

from instagrapi import Client
from instagrapi.exceptions import ClientLoginRequired, ClientError, UserNotFound

from .ig_config import IgConfig
from proxy_services import ProxyManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IgClient:
    """
    A class to manage Instagram client operations using a saved session.

    Attributes:
        client (instagrapi.Client): The Instagrapi Client object
        session_file (str): Path to the saved session file
        proxy_manager (ProxyManager): Manager for proxy operations
    """

    def __init__(self, account_id: str, proxy_manager: Optional[ProxyManager] = None):
        """
        Initialize Instagram client with account credentials.

        Args:
            account_id (str): The Instagram account identifier
        """
        self.account_id = account_id
        self.session_file = f"sessions/{account_id}_session.json"

        # Load config
        self.config = IgConfig(account_id)

        # Initialize proxy manager
        self.proxy_manager = proxy_manager or ProxyManager()

        # Initialize client
        self.client = Client()

        # Set device settings for iPhone 15
        self.device_settings = {
            "app_version": "302.1.0.34.111",
            "android_version": None,
            "android_release": None,
            "dpi": None,
            "resolution": "1290x2796",
            "manufacturer": "Apple",
            "device": "iPhone15,2",
            "model": "iPhone 15",
            "cpu": "ARM64",
            "version_code": "302110034",
            "user_agent": (
                "Instagram 302.1.0.34.111 "
                "(iPhone15,2; iOS 17_1_1; en_ES; en-ES; "
                "scale=3.00; 1290x2796; 302110034)"
            ),
            "locale": "en_ES",
            "timezone_offset": 3600,
        }

        # Set device settings
        self.client.set_device(self.device_settings)

        # Set initial proxy
        self.client.set_proxy(self.proxy_manager.get_current_proxy())

        # Load existing session if available
        if os.path.exists(self.session_file):
            os.remove(self.session_file)  # Remove old session to force new one
            logger.info(
                "Removed old session file to create new one with iPhone settings"
            )

    def _get_session_file_path(self) -> str:
        """Get the full path to the session file."""
        config_file_path = r"C:\Users\manue\Documents\GitHub007\sn-libraries\sessions"
        return str(Path(f"{config_file_path}/{self.account_id}_session.json").resolve())

    def load_session(self):
        """Load existing session and verify it's still valid."""
        self.client.load_settings(self.session_file)
        credentials = self.config.get_credentials()
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            raise ValueError("Username or password not set in the config file")
        self.client.login(username, password)

    def login(self):
        """Perform a fresh login and save the session."""
        credentials = self.config.get_credentials()
        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password:
            raise ValueError("Username or password not set in the config file")

        # Initialize client with device settings
        self.client = Client()
        self.client.set_device(self.device_settings)
        self.client.set_proxy(self.proxy_manager.get_current_proxy())

        # Perform login
        self.client.login(username, password)
        self.save_session()

    def save_session(self):
        """Save the current session to file."""
        self.client.dump_settings(self.session_file)

    def get_user_id(self, username: str) -> Optional[int]:
        """
        Fetches the user ID (pk) for a given Instagram username.

        Args:
            username (str): The Instagram username

        Returns:
            Optional[int]: The user's ID if found, None if not found
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

    def validate_session(self) -> bool:
        """Validate the current session and relogin if necessary."""
        try:
            logger.info("Validating Instagram session...")

            # Check if proxy needs rotation
            if self.proxy_manager.should_rotate():
                self.proxy_manager.rotate_if_needed()
                self.client.set_proxy(self.proxy_manager.get_current_proxy())

            # Verify proxy connection
            if not self.proxy_manager.validate_connection():
                logger.error("❌ Invalid proxy connection")
                return False

            # Test Instagram connection
            self.client.account_info()
            logger.info("✅ Session is valid")
            return True

        except Exception as e:
            logger.warning(f"❌ Session validation failed: {e}")
            try:
                logger.info("Attempting to reset session...")
                if self.reset_session():
                    self.client.account_info()
                    logger.info("✅ New session is valid")
                    return True
                else:
                    logger.error("❌ Session reset failed")
                    return False
            except Exception as e:
                logger.error(f"❌ Login failed after session reset: {e}")
                return False

    def reset_session(self) -> bool:
        """Reset the session with iPhone 15 settings and proxy."""
        try:
            logger.info("Resetting Instagram session...")
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.info("Removed existing session file")

            self.client = Client()
            self.client.set_device(self.device_settings)
            self.client.set_proxy(self.proxy_manager.get_current_proxy())

            credentials = self.config.get_credentials()
            username = credentials.get("username")
            password = credentials.get("password")

            if not username or not password:
                raise ValueError("Username or password not found in config")

            time.sleep(random.uniform(2, 5))
            self.client.login(username, password)
            self.save_session()

            logger.info("Successfully reset session")
            return True

        except Exception as e:
            logger.error(f"Failed to reset session: {e}")
            return False
