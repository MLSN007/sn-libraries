# ig_api_project/ig_post_manager.py

from typing import List, Optional
from shared_utils.data_models import SocialMediaPost
from ig_api_client import IgApiClient  
from datetime import datetime

class IgPostManager:
    """A class for managing Instagram post-related actions.

    This class provides methods for publishing, sharing, editing, deleting, and retrieving
    information about Instagram posts, Reels, and stories.
    """

    def __init__(self, api_client: IGApiClient) -> None:
        """Initializes the IGPostManager with the provided API client.

        Args:
            api_client: An instance of the InstagramAPIClient for API interaction.
        """
        self.api_client = api_client

    # Publish Methods
    def publish_post(self, message: str, media_paths: List[str]) -> Optional[SocialMediaPost]:
        """Publishes a regular Instagram post with one or more photos or videos.

        Args:
            message: The caption for the post.
            media_paths: A list of file paths to the media files (photos or videos).

        Returns:
            A SocialMediaPost object representing the published post, or None if publishing fails.
        """

        try:
            # 1. Upload media and get media IDs
            media_ids = [self.api_client.upload_media(path) for path in media_paths]

            # 2. Publish the post using the Instagram Graph API
            response = self.api_client.post_media(media_ids, caption=message)

            # 3. Extract relevant data from the API response
            post_id = response.get("id")
            timestamp = datetime.fromtimestamp(response.get("timestamp", 0))

            # 4. Create and return a SocialMediaPost object
            return SocialMediaPost(
                platform="IG",
                post_id=post_id,
                message=message,
                author=self.api_client.user_id,
                timestamp=timestamp,
                media_type=[self._get_media_type(path) for path in media_paths],  # Get media types
                media_urls=[self.api_client.get_media_url(media_id) for media_id in media_ids],
            )
        except Exception as e:  # Catch any exceptions during publishing
            print(f"Error publishing Instagram post: {e}")
            return None
    # ... (Other methods - Add 'pass' under each for now)

    def _get_media_type(self, media_path: str) -> str:
        """Helper function to determine the media type (photo or video) based on the file extension."""
        if media_path.endswith((".jpg", ".jpeg", ".png")):
            return "photo"
        elif media_path.endswith((".mp4", ".mov")):
            return "video"
        else:
            raise ValueError(f"Unsupported media type: {media_path}")

    def publish_reel(self, video_path: str, caption: str) -> Dict:
        """Publishes a Reel.

        Args:
            video_path: The file path to the video file.
            caption: The caption for the Reel.

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    def publish_story_photo(self, photo_path: str, options: Dict = None) -> Dict:
        """Publishes a photo to your story.

        Args:
            photo_path: The file path to the photo file.
            options: (Optional) A dictionary of additional options (e.g., stickers, text).

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    def publish_story_video(self, video_path: str, options: Dict = None) -> Dict:
        """Publishes a video to your story.

        Args:
            video_path: The file path to the video file.
            options: (Optional) A dictionary of additional options (e.g., stickers, text).

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    # Share Methods
    def share_reel_to_story(self, reel_id: str, options: Dict = None) -> Dict:
        """Shares a Reel to your story.

        Args:
            reel_id: The ID of the Reel to share.
            options: (Optional) A dictionary of additional options (e.g., stickers, text).

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    def share_reel_to_fb_page(self, reel_id: str, page_id: str) -> Dict:
        """Shares a Reel to your linked Facebook Page.

        Args:
            reel_id: The ID of the Reel to share.
            page_id: The ID of the Facebook Page to share to.

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    def share_post_to_story(self, post_id: str, options: Dict = None) -> Dict:
        """Shares an existing post to your story.

        Args:
            post_id: The ID of the post to share.
            options: (Optional) A dictionary of additional options (e.g., stickers, text).

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    # Edit Methods
    def edit_post(self, post_id: str, new_caption: str) -> Dict:
        """Edits the caption of an existing post.

        Args:
            post_id: The ID of the post to edit.
            new_caption: The new caption for the post.

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass
   
    def edit_reel(self, reel_id: str, new_caption: str) -> Dict:
        """Edits the caption of an existing reel.

        Args:
            reel_id: The ID of the reel to edit.
            new_caption: The new caption for the reel.

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    # Delete Methods
    def delete_post(self, post_id: str) -> Dict:
        """Deletes an existing post.

        Args:
            post_id: The ID of the post to delete.

        Returns:
            A dictionary containing the response from the Instagram API.
        """
        pass

    # Get Methods
    def get_post_insights(self, post_id: str) -> Dict:
        """Retrieves insights for a specific post.

        Args:
            post_id: The ID of the post.

        Returns:
            A dictionary containing the post insights data from the Instagram API.
        """
        pass

    def get_user_media(self, username: str) -> List[Dict]:
        """Retrieves recent media posted by a specific user.

        Args:
            username: The username of the user.

        Returns:
            A list of dictionaries, each containing information about a media item.
        """
        pass
