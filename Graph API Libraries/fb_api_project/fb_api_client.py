""" A client for interacting with the FbApiClient Class
    This class handles authentication, provides a GraphAPI object,
    and fetches the Facebook Page ID.
"""

import os
from typing import Dict, Optional
import facebook

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
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        page_id: Optional[str] = None,
        api_version: str = "3.1",
    ) -> None:

        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.page_id = page_id
        self.api_version = api_version
        self._graph = None

        if not (app_id and app_secret and access_token):
            credentials = self._load_credentials()
            self.app_id = credentials["app_id"]
            self.app_secret = credentials["app_secret"]
            self.access_token = credentials["access_token"]
            self.page_id = credentials["page_id"]



    @staticmethod
    def load_credentials(
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        page_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Loads credentials from environment variables or provided arguments.

        Args: 
            app_id (str, optional): Your Facebook App ID.
            app_secret (str, optional): Your Facebook App Secret.
            access_token (str, optional): Your long-lived user access token.
            page_id (str, optional): The ID of the page you want to manage.

        Returns:
            Dict[str, str]: A dictionary containing the keys 'app_id', 'app_secret',
                            'access_token', and 'page_id'.

        Raises:
            ValueError: If credentials are not found in either location.
        """

        # Check if any arguments are provided
        if any([app_id, app_secret, access_token, page_id]):
            # Use provided arguments if available
            return {
                "app_id": app_id or os.environ.get("FB_ES_App_id"),
                "app_secret": app_secret or os.environ.get("FB_ES_App_secret"),
                "access_token": access_token or os.environ.get("FB_ES_App_token"),
                "page_id": page_id or os.environ.get("FB_ES_Pg_id"),
            }
        else:
            # Use environment variables if no arguments are provided
            try:
                return {
                    "app_id": os.environ.get("FB_ES_App_id"),
                    "app_secret": os.environ.get("FB_ES_App_secret"),
                    "access_token": os.environ.get("FB_ES_App_token"),
                    "page_id": os.environ.get("FB_ES_Pg_id"),
                }
            except KeyError as e:
                raise ValueError(f"Environment variable {e} not found.") from e




    def get_graph_api_object(self) -> facebook.GraphAPI:
        """Retrieves or creates a GraphAPI object for making API calls."""

        if self._graph is None:
            self._graph = facebook.GraphAPI(
                access_token=self.access_token, version=self.api_version
            )
        return self._graph
