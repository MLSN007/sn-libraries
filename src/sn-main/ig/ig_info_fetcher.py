"""Fetches Instagram user information using the HikerAPI.

This module provides a class, `IgInfoFetcher`, that facilitates the retrieval of
Instagram user information using the HikerAPI. The class allows you to fetch
user information for single or multiple users, and optionally save it to a JSON
file. 
"""


import os
import json
import logging
from typing import Dict, List, Optional
from hikerapi import Client

DEFAULT_OUTPUT_FILE = "instagram_info.json"

class IgInfoFetcher:
    """Fetches Instagram user information using the HikerAPI.

    Attributes:
        client (hikerapi.Client): An instance of the HikerAPI client.

    Args:
        api_key (str, optional): Your HikerAPI key. Defaults to the value of the environment variable "HikerAPI_key".

    Raises:
        ValueError: If the "HikerAPI_key" environment variable is not set.
    """


    def __init__(self, api_key: Optional[str] = os.environ.get("HikerAPI_key")) -> None:
        """
        Initializes the IgInfoFetcher with the HikerAPI key.

        Args:
            api_key (str, optional): Your HikerAPI key. Defaults to the value of the environment variable HikerAPI_key.

        Raises:
            ValueError: If the HikerAPI_key environment variable is not set.
        """
        if not api_key:
            raise ValueError("HikerAPI_key environment variable not found.")
        self.client = Client(token=api_key)

    def fetch_info(self, username: str) -> Optional[Dict]:
        """
        Fetches information for a single Instagram user.

        Args:
            username (str): The Instagram username.

        Returns:
            Optional[Dict]: A dictionary containing the user's information if successful, otherwise None.
        """
        try:
            user_info = self.client.user_by_username_v2(username)
            if user_info["status"] == "ok":
                return user_info
            else:
                logging.error("Error fetching data for %s: %s", username, user_info.get("error"))
                return None

        except Exception as e:
            logging.error("Unexpected error fetching data for %s: %s", username, e)
        return None

    def fetch_and_save_info(self, usernames: List[str], output_file: str = DEFAULT_OUTPUT_FILE) -> None:
        """
        Fetches information for multiple Instagram users and saves it to a JSON file.

        Args:
            usernames (List[str]): A list of Instagram usernames.
            output_file (str, optional): The path to the output JSON file. Defaults to "instagram_info.json".
        """
        all_info_data = []
        for username in usernames:
            info_data = self.fetch_info(username)
            if info_data:
                all_info_data.append(info_data)
            else:
                logging.warning("Failed to fetch info for %s", username)

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_info_data, f, ensure_ascii=False, indent=4)
            logging.info("Saved %d profiles to %s", len(all_info_data), output_file)
        except IOError as e:
            logging.error("Error saving data to file %s: %s", output_file, e)