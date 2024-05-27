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


    def get_groups_followed(
        self, page_or_user_id: str, fields: str = "id,name,description"
    ) -> List[Dict[str, Any]]:
        """Retrieves basic information about the groups followed by a page or user.

        Args:
            page_or_user_id (str): The ID of the page or user.
            fields (str, optional): Comma-separated list of fields to include (e.g., "id,name,description").

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing group information, or an empty list if none are found.
        """
        graph = self.api_client.get_graph_api_object()
        try:
            # Fetch groups followed by the page or user
            groups_data = graph.get_connections(
                id=page_or_user_id,
                connection_name="groups",
                fields=fields,
            )
            return groups_data["data"]  # Extract group data from the response

        except facebook.GraphAPIError as e:
            print(f"Error retrieving groups followed: {e.message}")
            return []  # Return an empty list on error

