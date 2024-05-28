"""
utils.py

This module provides utility functions for interacting with the Facebook Graph API, 
including:

- get_group_info: Retrieves information about a Facebook group.
- get_page_or_user_info: Retrieves information about a Facebook page or user.
- FacebookAPIClient: A client class for managing Facebook API authentication and interactions.
"""

import logging
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import facebook


logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG




from facebook_api_client import FacebookAPIClient

class Utils:
    """A class containing utility functions for your Facebook API project."""

    def __init__(self, api_client: "FacebookAPIClient") -> None:
        self.api_client = api_client



    @staticmethod
    def get_group_info(
        api_client: FacebookAPIClient, group_id: str, fields: str = "name,description,icon"
    ) -> Dict[str, Any]:
        """Retrieves basic information about a Facebook group.

        Args:
            api_client (FacebookAPIClient): An instance of the FacebookAPIClient class.
            group_id (str): The ID of the Facebook group.
            fields (str, optional): Comma-separated list of fields to include
                                    (e.g., "name,description").

        Returns:
            Dict[str, Any]: A dictionary containing the group's information.
        """
        graph = api_client.get_graph_api_object()  # Use the API client to get the graph object
        try:
            group_data = graph.get_object(id=group_id, fields=fields)
            return group_data
        except facebook.GraphAPIError as e:
            print(f"Error retrieving group info: {e.message}")
            return {}

    @staticmethod
    def get_page_id(page_name: str) -> Optional[str]:
        """Attempts to scrape the User ID of a Facebook Page by its name."""

        url = f"https://www.facebook.com/{page_name}"
        try:
            response = requests.get(url)
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

    @staticmethod
    def get_page_or_user_info(
        api_client: FacebookAPIClient,
        page_or_user_id: str,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Retrieves information about a Facebook page or user.

        Args:
            api_client (FacebookAPIClient): An instance of the FacebookAPIClient class.
            page_or_user_id (str): The ID of the page or user.
            fields (List[str], optional): A list of fields to include in the response. Defaults to None, which fetches the default fields 'id', 'name', and 'about'.

        Returns:
            Dict[str, Any]: A dictionary containing the requested information about the page or user, 
                            or an empty dictionary if there was an error.
        """

        graph = api_client.get_graph_api_object()
        default_fields = ["id", "name", "about"]
        fields = fields or default_fields
        try:
            # Fetch page/user data, joining the fields list with commas for the API
            data = graph.get_object(id=page_or_user_id, fields=",".join(fields))
            return data
        except facebook.GraphAPIError as e:
            print(f"Error retrieving page/user info: {e.message}")
            return {}

