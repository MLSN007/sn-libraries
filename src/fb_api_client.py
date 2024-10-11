"""A client for interacting with the Facebook Graph API.

This class handles authentication (using either provided credentials or 
environment variables), provides a convenient `GraphAPI` object for making 
requests, and stores the Facebook Page ID you intend to interact with.

Attributes:
    app_id (str): Your Facebook App ID.
    app_secret (str): Your Facebook App Secret.
    access_token (str): Your long-lived user access token.
    page_id (str): The ID of the Facebook Page you want to manage. This is used 
        in various methods to target specific Page actions.
    api_version (str): The Graph API version in use (default: '3.1').
    _graph (Optional[facebook.GraphAPI]): The GraphAPI object for making requests. 
        Initialized lazily when first needed.
"""

import os
from typing import Dict, Optional, Any
import requests


class FbApiClient:
    """A client for interacting with the Facebook Graph API.

    This class handles authentication, and provides a GraphAPI object,

    Args:
        app_id (str, optional): Your Facebook App ID.
        app_secret (str, optional): Your Facebook App Secret.
        access_token (str, optional): Your long-lived user access token.
        page_id (str, optional): The ID of the page you want to manage
        api_version (str, optional): The Graph API version to use (default: 'v20.0').

    Attributes:
        app_id (str): Your Facebook App ID.
        app_secret (str): Your Facebook App Secret.
        access_token (str): Your long-lived user access token.
        page_id (str): The ID of the page you want to manage
        api_version (str): The Graph API version in use.
        _graph (Optional[facebook.GraphAPI]): The GraphAPI object for making requests.

    """

    def __init__(
        self,
        access_token: str,
        api_version: str = "v20.0",
    ) -> None:

        self.access_token = access_token
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}/"

    def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params["access_token"] = self.access_token

        response = requests.request(method, url, params=params, json=data)
        response.raise_for_status()
        return response.json()

    def get_object(
        self, object_id: str, fields: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {}
        if fields:
            params["fields"] = fields
        return self.make_request(object_id, params=params)

    def get_connections(
        self, object_id: str, connection_name: str, **kwargs
    ) -> Dict[str, Any]:
        endpoint = f"{object_id}/{connection_name}"
        return self.make_request(endpoint, params=kwargs)

    def put_object(
        self, parent_object: str, connection_name: str, **data
    ) -> Dict[str, Any]:
        endpoint = f"{parent_object}/{connection_name}"
        return self.make_request(endpoint, method="POST", data=data)

    # Add more methods as needed
