import json
import logging
from typing import Optional

class Config:
    """
    Configuration class to load settings from a JSON file.
    """

    def __init__(self, config_file_path="config.json"):
        """
        Initialize the Config class.

        Args:
            config_file_path: Path to the JSON configuration file (default: "config.json").
        """
        self.config_file_path = config_file_path
        self.load_config()

    def load_config(self):
        """
        Load configuration settings from the JSON file.

        If the config file is not found, it logs a warning and initializes an empty configuration dictionary.
        """
        try:
            with open(self.config_file_path, "r", encoding="utf-8") as config_file:
                self.config = json.load(config_file)

        except FileNotFoundError:
            self.config = {}  # Use empty dictionary if config file not found
            logging.warning(
                f"Config file not found at {self.config_file_path}. Using default values."
            )

    def get(self, key, default=None):
        """
        Get a configuration value by key.

        Args:
            key: The key to retrieve the value for.
            default: The default value to return if the key is not found (default: None).

        Returns:
            The configuration value if found, otherwise the default value.
        """
        return self.config.get(key, default)
