import os
import logging
from typing import Optional, Dict


logger = logging.getLogger(__name__)


class IgConfig:
    """Configuration class for Instagram credentials using environment variables.

    This class manages Instagram credentials for different accounts using environment variables:
    - Username is stored in IG_{account}_user
    - Password is stored in IG_{account}_psw

    Example:
        For account 'JK':
        - Username is stored in IG_JK_user
        - Password is stored in IG_JK_psw
    """

    def __init__(self, account_id: str):
        """Initialize Instagram configuration for a specific account.

        Args:
            account_id (str): The identifier for the Instagram account (e.g., 'JK')
        """
        self.account_id = account_id
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from environment variables."""
        try:
            # Get username from environment variable
            self.username = os.getenv(f"IG_{self.account_id}_user")
            if not self.username:
                logger.error(
                    f"Environment variable IG_{self.account_id}_user not found"
                )
                raise ValueError(f"Username not set for account {self.account_id}")

            # Get password from environment variable
            self.password = os.getenv(f"IG_{self.account_id}_psw")
            if not self.password:
                logger.error(f"Environment variable IG_{self.account_id}_psw not found")
                raise ValueError(f"Password not set for account {self.account_id}")

            logger.info(
                f"Successfully loaded credentials for account {self.account_id}"
            )

        except Exception as e:
            logger.error(
                f"Error loading config for account {self.account_id}: {str(e)}"
            )
            raise

    def get_credentials(self) -> Dict[str, str]:
        """Get Instagram credentials from config."""
        return {
            "username": self.username,
            "password": self.password
        }
