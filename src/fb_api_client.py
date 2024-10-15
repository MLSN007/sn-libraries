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
import facebook
import traceback


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

    def __init__(self, credentials: Dict[str, str]):
        self.credentials = credentials
        self.graph = facebook.GraphAPI(
            access_token=credentials["access_token"], version="3.1"
        )

    def make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        if "access_token" not in params:
            params["access_token"] = self.access_token

        print(f"Making {method} request to {url}")
        print(f"Params: {params}")
        print(f"Data: {data}")
        print(f"Files: {files.keys() if files else None}")

        response = requests.request(method, url, params=params, data=data, files=files)
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")
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

    def put_object(self, parent_object: str, connection_name: str, **data):
        try:
            print(f"Putting object to {parent_object}/{connection_name}")
            print(f"Data: {data}")
            result = self.graph.put_object(parent_object, connection_name, **data)
            print(f"Put object result: {result}")
            return result
        except facebook.GraphAPIError as e:
            print(f"Facebook API Error in put_object: {e}")
            print("Traceback:")
            traceback.print_exc()
            raise

    def put_photo(self, image, message=None, album_path="me/photos", **kwargs):
        try:
            print(f"Putting photo to {album_path}")
            print(f"Message: {message}")
            print(f"Additional kwargs: {kwargs}")
            result = self.graph.put_photo(
                image=image, message=message, album_path=album_path, **kwargs
            )
            print(f"Put photo result: {result}")
            return result
        except facebook.GraphAPIError as e:
            print(f"Facebook API Error in put_photo: {e}")
            print(f"Error type: {type(e)}")
            print(f"Error code: {getattr(e, 'code', 'N/A')}")
            print(f"Error subcode: {getattr(e, 'subcode', 'N/A')}")
            print(f"Error message: {getattr(e, 'message', 'N/A')}")
            print("Traceback:")
            traceback.print_exc()
            raise

    # Add more methods as needed
