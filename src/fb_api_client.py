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
from requests.exceptions import RequestException
import logging

logger = logging.getLogger(__name__)


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

    def __init__(self, credentials: Dict[str, str], api_version: str = "21.0"):
        self.credentials = credentials
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/v{api_version}/"

    def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"  # Fix URL construction
        headers = {"Authorization": f"Bearer {self.credentials['access_token']}"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=data, files=files)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            if e.response is not None:
                logger.error(f"Response content: {e.response.content}")
            raise

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

    def put_object(self, parent_object: str, connection_name: str, **data):
        endpoint = f"{parent_object}/{connection_name}"
        return self.make_request(endpoint, method="POST", data=data)

    def put_photo(self, image, message=None, album_path="me/photos", **kwargs):
        files = {"source": image}
        data = kwargs.copy()
        if message:
            data["message"] = message
        return self.make_request(album_path, method="POST", files=files, data=data)

    # Add more methods as needed
