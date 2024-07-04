import json
import logging
from typing import Optional, Any

class Config:
    """Configuration class for loading settings from a JSON file.

    This class provides a simple interface for loading configuration settings from a
    JSON file. If the file doesn't exist, it logs a warning and uses an empty
    dictionary as the default configuration.

    Attributes:
        config_file_path (str): The path to the JSON configuration file.
        config (dict): The loaded configuration dictionary.
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
        """Loads configuration settings from the JSON file.

        If the file is not found, logs a warning and initializes an empty configuration.
        """

        try:
            with open(self.config_file_path, "r", encoding="utf-8") as config_file:
                self.config = json.load(config_file)

        except FileNotFoundError:
            self.config = {}  # Use empty dictionary if config file not found
            logging.warning(
                f"Config file not found at {self.config_file_path}. Using default values."
            )
        except json.JSONDecodeError as e: # Added JSONDecodeError handling
            self.config = {}
            logging.error(f"Error loading config file: {e}")

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Retrieves a configuration value by key.

        Args:
            key (str): The configuration key.
            default (Any, optional): The default value to return if the key is not found.

        Returns:
            Any: The configuration value associated with the key, or the default value if the key is not found.
        """
        return self.config.get(key, default)
