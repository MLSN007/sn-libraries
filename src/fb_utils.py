"""Utility functions for interacting with the Facebook Graph API.

This module provides various helper functions for working with the Facebook Graph
API, such as retrieving information about groups and pages/users.

Classes:
    FbUtils: A class containing utility functions for Facebook API interactions.
        
"""

import logging
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import facebook

from fb_api_client import FbApiClient


logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG


class FbUtils:
    """A class containing utility functions for Facebook API interactions.

    This class requires an instance of `FbApiClient` to be passed during
    initialization for handling API authentication and requests.

    Args:
        api_client (FbApiClient): An instance of the FbApiClient for making API requests.
    """

    def __init__(self, api_client: "FbApiClient") -> None:
        self.api_client = api_client

    @staticmethod
    def get_page_id(page_name: str) -> Optional[str]:
        """Attempts to scrape the User ID of a Facebook Page by its name.

        Args:
            page_name (str): The name of the Facebook page.

        Returns:
            Optional[str]: The ID of the page if found, or None if not found or an error occurs.
        """

        url = f"https://www.facebook.com/{page_name}"
        try:
            response = requests.get(url, timeout=10)  # Add timeout of 10 seconds
            response.raise_for_status()  # Raise an exception for bad responses
            soup = BeautifulSoup(response.text, "html.parser")

            # Look for the User ID in likely places (adjust as needed)
            user_id_match = soup.find("meta", property="al:ios:url")
            if user_id_match:
                user_id = user_id_match["content"].split(":")[-1]
                return user_id
        except (requests.RequestException, AttributeError, IndexError):
            pass  # Handle errors (page not found, ID not in expected format, etc.)

        return None  # Return None if the ID couldn't be found

    def get_group_info(
        self, group_id: str, fields: str = "name,description,icon"
    ) -> Dict[str, Any]:
        """Retrieves basic information about a Facebook group.

        Args:
            group_id (str): The ID of the Facebook group.
            fields (str, optional): Comma-separated list of fields to include
            (e.g., "name,description,icon"). Defaults to "name,description,icon".

        Returns:
            Dict[str, Any]: A dictionary containing the group's information, or an empty dictionary if an error occurs.
        """
        graph = self.api_client.get_graph_api_object()
        try:
            group_data = graph.get_object(id=group_id, fields=fields)
            return group_data
        except facebook.GraphAPIError as e:
            print(f"Error retrieving group info: {e}")
            return {}
