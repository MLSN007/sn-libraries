"""
utils.py

This module provides utility functions for interacting with the Facebook Graph API, 
including:

- get_group_info: Retrieves information about a Facebook group.
- get_page_or_user_info: Retrieves information about a Facebook page or user.
- FacebookAPIClient: A client class for managing Facebook API authentication and interactions.
"""

import os
from typing import Dict, Any, List
import facebook

import logging
logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG




from facebook_api_client import FacebookAPIClient

class Utils:
    """A class containing utility functions for your Facebook API project."""

    def __init__(self, api_client: "FacebookAPIClient") -> None:
        self.api_client = api_client


    def search_groups_by_name(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Searches for Facebook groups by name and returns their basic information.

        Args:
            query (str): The search query (group name).
            limit (int, optional): The maximum number of groups to return (default: 10).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing group information (id, name, privacy), 
                                or an empty list if no groups are found.
        """
        graph = self.api_client.get_graph_api_object()
        try:
            search_results = graph.get_object(
                id="search",
                q=query,
                type="group",
                limit=limit,
                fields="id,name,privacy"
            )
            print(search_results)
            
            return search_results.get("data", [])  # Return empty list if no groups found
        except facebook.GraphAPIError as e:
            logging.error(f"Error searching for groups: {e}")  # Log the error
            return []



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
    def get_page_or_user_info(
        api_client: FacebookAPIClient, page_or_user_id: str, fields: str = "name,about"
    ) -> Dict[str, Any]:
        """Retrieves basic information about a Facebook page or user.

        Args:
            api_client (FacebookAPIClient): An instance of the FacebookAPIClient class.
            page_or_user_id (str): The ID of the page or user.
            fields (str, optional): Comma-separated list of fields to include (e.g., "name,about").

        Returns:
            Dict[str, Any]: A dictionary containing the page or user's information.
        """
        graph = api_client.get_graph_api_object()
        try:
            data = graph.get_object(id=page_or_user_id, fields=fields)
            return data
        except facebook.GraphAPIError as e:
            print(f"Error retrieving page/user info: {e.message}")
            return {}


