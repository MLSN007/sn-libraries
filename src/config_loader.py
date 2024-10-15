import os
import json


class ConfigLoader:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self.load_config()
        self.credentials = self.load_credentials()

    def load_config(self) -> dict:
        print(f"Loading Facebook configuration from: {self.config_file}")
        with open(self.config_file, "r") as f:
            config = json.load(f)
        print("Facebook configuration loaded successfully")
        return config

    def load_credentials(self) -> dict:
        print("Loading Facebook credentials from environment variables")
        credentials = {}
        try:
            for key in [
                "app_id",
                "app_secret",
                "access_token",
                "page_id",
                "user_id",
                "user_token",
            ]:
                credentials[key] = os.environ[self.config[key]]
                print(
                    f"Loaded {key}: {credentials[key][:5]}..."
                )  # Print first 5 characters for security
        except KeyError as e:
            print(
                f"Error: Environment variable {e} not set. Please set it before running the script."
            )
            exit(1)
        print("Facebook credentials loaded successfully")
        return credentials
