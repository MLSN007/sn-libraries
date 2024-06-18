# ig-api/ig_media_utils.py

from os.path import splitext
import requests
import mimetypes
from ig_api_client import IgApiClient

def upload_media(api_client: IgApiClient, media_path: str) -> str:
    """Uploads a photo or video to Instagram and returns the media ID.

    Args:
        api_client: An instance of the IgApiClient class.
        media_path: The local file path to the photo or video to upload.

    Returns:
        str: The ID of the uploaded media, or None if the upload fails.
    """

    # 1. Determine media type based on file extension
    ext = splitext(media_path)[1].lower()  # Get the file extension in lowercase
    media_type = "IMAGE" if ext in (".jpg", ".jpeg", ".png") else "VIDEO"

    # 2. Prepare API endpoint and parameters
    endpoint = f"{api_client.base_url}/media"
    params = {
        "image_url": media_path,  # For photos
        "caption": "Uploaded via API"  # Optional caption
    }
    if media_type == "VIDEO":
        params["media_type"] = "VIDEO"

    # 3. Prepare file data for videos
    files = None
    if media_type == "VIDEO":
        with open(media_path, "rb") as video_file:
            files = {"media": (media_path, video_file, "video/mp4")}  # Adjust mimetype if needed

    # 4. Make the API request
    try:
        response = requests.post(endpoint, params=params, files=files)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()

        if "id" in response_data:
            return response_data["id"]  # Return the media ID
        else:
            raise Exception(f"Media upload failed: {response_data.get('error', response_data)}")
    except requests.RequestException as e:
        raise Exception(f"Error uploading media: {e}")
