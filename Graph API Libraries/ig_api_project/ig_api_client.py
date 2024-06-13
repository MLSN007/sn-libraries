# ig_api_project/ig_api_client.py

import requests
from typing import List, Dict, Optional
from ig_media_utils import upload_media

class IgApiClient:
    # ... (Other imports and class docstring)

    def __init__(self, access_token: str, instagram_business_account_id: str):
        # ... (Initialization logic)

    def _make_api_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        # ... (Existing method for making API requests)
    
    def post_media(self, media_ids: List[str], caption: str) -> Dict:
        """Publishes a post with the given media IDs and caption.

        Args:
            media_ids: A list of media IDs obtained by uploading media using the `upload_media` function.
            caption: The caption for the post.

        Returns:
            A dictionary containing the response from the Instagram API.
        """

        endpoint = f"{self.base_url}/media_publish"
        params = {
            "creation_id": media_ids[0],  # Use the first media ID as the creation ID
            "caption": caption
        }
        return self._make_api_request(endpoint, params)

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
