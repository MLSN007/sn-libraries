# ig-api/ig_api_client.py

import requests
from typing import List, Dict, Optional


class IgApiClient:
    # ... (Other imports and class docstring)

    def __init__(self, access_token: str, instagram_business_account_id: str):
        """Initializes the IgApiClient."""
        self.access_token = access_token
        self.instagram_business_account_id = instagram_business_account_id
        self.base_url = f"https://graph.facebook.com/v20.0/{self.instagram_business_account_id}"  # Use the correct API version



    def _make_api_request(self, endpoint: str, params: Optional[dict] = None) -> Dict:
        url = f"{self.base_url}/{endpoint}"
        if params is None:
            params = {}
        params["access_token"] = self.access_token

        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        json_response = response.json()
        
        # Check for Instagram API errors
        if "error" in json_response:
            error_code = json_response["error"]["code"]
            error_message = json_response["error"]["message"]
            raise Exception(f"Instagram API Error ({error_code}): {error_message}")
        
        return json_response
    
    def post_media(self, media_ids: List[str], caption: str = "") -> Dict:
        """Publishes a post with the given media IDs and caption."""

        if not media_ids:
            raise ValueError("At least one media ID is required for publishing a post.")

        try:
            endpoint = f"{self.base_url}/media_publish"
            params = {
                "creation_id": media_ids[0],
                "caption": caption
            }
            return self._make_api_request(endpoint, params)
        except Exception as e:  # Catch specific Instagram API errors here
            print(f"Error publishing Instagram post: {e}")
            return {}

    # ... (Add other methods for Instagram API interactions)

    def get_media_url(self, media_id: str) -> str:
        """Retrieves the URL of the given media.

        Args:
            media_id: The ID of the media.

        Returns:
            The URL of the media.
        """
        endpoint = f"/{media_id}"
        params = {"fields": "media_url"}
        response = self._make_api_request(endpoint, params)
        return response.get("media_url")
