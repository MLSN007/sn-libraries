# ig-api/ig_media_utils.py

import requests

def upload_media(api_client: IgApiClient, media_path: str) -> str:
    """Uploads media to Instagram and returns the media ID."""

    # Determine media type (photo or video) based on file extension
    media_type = ...  # Implement logic to determine the type

    # Prepare request data and headers
    endpoint = f"{api_client.base_url}/media"
    params = {"image_url": media_path} if media_type == "photo" else {"media_type": "VIDEO", "video_url": media_path}
    files = ...  # Prepare file data (if needed for videos)

    # Make API request
    response = requests.post(endpoint, params=params, files=files)
    response.raise_for_status()

    # Extract media ID from response
    media_id = response.json()["id"]
    return media_id
