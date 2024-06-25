"""
ig_info_fetcher.py: Fetches Instagram user information using the HikerAPI.
"""

import os
import json
import logging
from hikerapi import Client


class IgInfoFetcher:
    """A class for fetching Instagram user information using the HikerAPI."""

    def __init__(self, api_key=os.environ.get("HikerAPI_key")):
        """
        Initializes the IgInfoFetcher with the HikerAPI key.

        Args:
            api_key (str, optional): Your HikerAPI key. Defaults to the value of the environment variable HIKER_API_KEY.

        Raises:
            ValueError: If the HIKER_API_KEY environment variable is not set.
        """

        if not api_key:
            raise ValueError("HikerAPI_key environment variable not found.")
        self.client = Client(token=api_key)

    def fetch_info(self, username):
        """
        Fetches information for a single Instagram user.

        Args:
            username (str): The Instagram username.

        Returns:
            dict or None: A dictionary containing the user's information if successful, otherwise None.
        """
        try:
            user_info = self.client.user_by_username_v2(username)
            if user_info["status"] == "ok":
                return user_info
            else:
                logging.error("Error fetching data for %s: %s", username, user_info.get("error"))
        except Exception as e:
            logging.error("Error fetching data for %s: %s", username, e)
        return None  # Return None on error


    def fetch_and_save_info(self, usernames, output_file="instagram_info.json"):
        """
        Fetches information for multiple Instagram users and saves it to a JSON file.

        Args:
            usernames (list): A list of Instagram usernames.
            output_file (str, optional): The path to the output JSON file. Defaults to "instagram_info.json".
        """
        all_info_data = []
        for username in usernames:
            info_data = self.fetch_info(username)
            if info_data:
                all_info_data.append(info_data)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_info_data, f, ensure_ascii=False, indent=4)
        logging.info("Saved %d profiles to %s", len(all_info_data), output_file)
