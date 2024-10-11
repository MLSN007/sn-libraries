""" FbPostManager (in fb_post_manager.py):
    A class for managing Facebook post-related actions.

    This class provides methods to interact with Facebook posts, including retrieving 
    posts, publishing posts (text and photo), and more. 

    Note: Some methods are still under development (marked as PENDING).

    Args:
        api_client (FbApiClient): An instance of the FbApiClient for handling 
            Facebook Graph API interactions.
    


    Implemented Methods:
    get_latest_posts(self):
    get_all_post_ids(self): Retrieves all post IDs from the Facebook Page.
    publish_text_post(self, message): Publishes a text-only post.
    publish_photo_post(self, message, photo_path): Publishes a post with a photo and text.
    
    OTHER METHODS PENDING PROGRAMMING
    publish_multi_photo_post(self, message, photo_paths): Publishes a post with multiple photos and text.
    publish_video_post(self, message, video_path): Publishes a post with a video and text.
    delete_post(self, post_id): Deletes a specific post.
    like_post(self, post_id): Likes a specific post. (my own or third party) (PENDING)
    like_photo(Self, photo_if) or Like Media????????????

"""

from typing import Dict, Optional, Any, List
import time
import json
import requests


class FbPostManager:
    """Manages Facebook post-related actions.

    Args:
        api_client (FacebookAPIClient): An instance of the FacebookAPIClient for API interaction.
    """

    def __init__(self, api_client: "FacebookAPIClient") -> None:
        self.api_client = api_client

    def get_latest_posts(self, page_id: str, num_posts: int = 10, fields: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Retrieves the latest posts from a Facebook Page without attachment details.

        Args:
            page_id (str): The ID of the Facebook Page.
            num_posts (int, optional): The number of posts to retrieve (default: 10, max: 100).
            fields (str, optional): Comma-separated list of fields to include (default: basic fields).

        Returns:
            Optional[List[Dict[str, Any]]]: A list of dictionaries, each representing a post,
                or None if an error occurs.
        """

        default_fields = "id,message,created_time,permalink_url,likes.summary(true),comments.summary(true)"
        fields = fields or default_fields

        try:
            posts = self.api_client.get_connections(
                page_id,
                "posts",
                fields=fields,
                limit=num_posts
            )
            return posts.get("data")
        except requests.RequestException as e:
            print(f"Error retrieving latest posts: {e}")
            return None

    def get_post_by_id(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific Facebook post by its ID, including message and media.

        Args:
            post_id (str): The ID of the post.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the post data (including
                attachments), or None if not found or an error occurs.
                _____________________________________________________________

                PENDING TO GET INFORMATION ABOUT SHARES OF THE POST
                __________________________________________________________

            If the post is not found or an error occurs, None is returned.
        """

        fields = (
            "id,message,created_time,permalink_url,"
            "likes.summary(true),comments.summary(true),attachments"
        )
        try:
            post_data = self.api_client.get_object(post_id, fields=fields)
            # Process attachments (if present)
            if "attachments" in post_data:
                attachments = post_data["attachments"]["data"]
                for attachment in attachments:
                    if attachment.get("media_type") == "photo":
                        photo_url = attachment["media"]["image"]["src"]
                        print(f"Found photo: {photo_url}")
                    elif attachment.get("media_type") == "video":
                        video_url = attachment["media"]["source"]
                        print(f"Found video: {video_url}")
            return post_data
        except requests.RequestException as e:
            print(f"Error retrieving post by ID: {e}")
            return None

    def get_post_likes(self, post_id: str) -> List[Dict[str, Any]]:
        """Retrieves information about users who liked a specific Facebook post.

        Handles permission limitations gracefully.

        Args:
            post_id (str): The ID of the post.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing either:
                - User's name and ID (if permission is granted)
                - {"unknown": True} if user information is not accessible
        """
        try:
            likes_response = self.api_client.get_connections(post_id, "likes")
            likes_data = likes_response.get("data", [])
            likes = []
            for like_data in likes_data:
                if "name" in like_data and "id" in like_data:
                    likes.append(like_data)
                else:
                    likes.append({"unknown": True})
            return likes
        except requests.RequestException as e:
            print(f"Error retrieving likes for post {post_id}: {e}")
            return []

    def get_post_shares(self, post_id: str) -> List[Dict]:
        """Retrieves shared post data for a specific Facebook post.

        Args:
            post_id (str): The ID of the post.

        Returns:
            List[Dict]: A list of dictionaries, each representing a shared post. Returns 0 on error.
        """
        try:
            shared_posts = self.api_client.get_connections(post_id, "sharedposts")
            return shared_posts.get("data", [])
        except requests.RequestException as e:
            print(f"Error retrieving shares for post {post_id}: {e}")
            return []

    def publish_text_post(self, page_id: str, message: str) -> Optional[Dict]:
        """Publishes a text-only (or photo) post on a Facebook Page.

        Args:
            page_id (str): The ID of the page to publish the post on.
            message (str): The text content of the post.
            photo_path (str, optional): The path to the photo file (for publish_photo_post only).

        Returns:
            Optional[Dict]: A dictionary containing post details if successful, or None if an error occurs.
        """
        try:
            post = self.api_client.put_object(page_id, "feed", message=message)
            print(f"Post published successfully. Post ID: {post['id']}")
            return post
        except requests.RequestException as e:
            print(f"Error publishing post: {e}")
            return None

    def publish_photo_post(self, page_id: str, message: str, photo_path: str) -> Optional[Dict]:
        """Publishes a text-only (or photo) post on a Facebook Page.

        Args:
            page_id (str): The ID of the page to publish the post on.
            message (str): The text content of the post.
            photo_path (str, optional): The path to the photo file (for publish_photo_post only).

        Returns:
            Optional[Dict]: A dictionary containing post details if successful, or None if an error occurs.
        """
        try:
            with open(photo_path, "rb") as image_file:
                files = {'source': image_file}
                data = {'message': message}
                post = self.api_client.put_object(page_id, "photos", files=files, **data)
            print(f"Post with photo published successfully. Post ID: {post['post_id']}")
            return post
        except requests.RequestException as e:
            print(f"Error publishing post with photo: {e}")
            return None

    def publish_multi_photo_post(
        self, page_id: str, message: str, photo_paths: List[str]
    ) -> Optional[Dict]:
        """Publishes a post with multiple photos to a Facebook Page."""
        try:
            photo_ids = []
            for photo_path in photo_paths:
                with open(photo_path, "rb") as photo_file:
                    time.sleep(2)  # sleep to avoid Facebook rate limiting
                    photo = self.api_client.put_object(
                        page_id,
                        "photos",
                        published=False,
                        files={"source": photo_file}
                    )
                    photo_ids.append({"media_fbid": photo["id"]})

            post = self.api_client.put_object(
                page_id,
                "feed",
                message=message,
                attached_media=photo_ids
            )
            print(f"Multi-photo post published successfully. Post ID: {post['id']}")
            return post
        except requests.RequestException as e:
            print(f"Error publishing multi-photo post: {e}")
            return None

    def publish_video_post(
        self, page_id: str, message: str, video_path: str, title: Optional[str] = None
    ) -> Optional[Dict]:
        """Publishes a video post to a Facebook Page."""
        try:
            with open(video_path, "rb") as video_file:
                video_data = {
                    "message": message,
                    "source": video_file,
                }
                if title:
                    video_data["title"] = title

                post = self.api_client.put_object(
                    page_id,
                    "videos",
                    files={"source": video_file},
                    **video_data
                )
            print(f"Video post published successfully. Post ID: {post.get('id')}")
            return post
        except requests.RequestException as e:
            print(f"Error publishing video post: {e}")
            return None

    def publish_reel(
        self, page_id: str, message: str, video_path: str, title: Optional[str] = None
    ) -> Optional[Dict]:
        """Publishes a reel to a Facebook Page."""
        try:
            with open(video_path, "rb") as video_file:
                reel_data = {
                    "message": message,
                    "source": video_file,
                    "is_reel": True,
                }
                if title:
                    reel_data["title"] = title

                reel = self.api_client.put_object(
                    page_id,
                    "videos",
                    files={"source": video_file},
                    **reel_data
                )
            print(f"Reel published successfully. Reel ID: {reel['id']}")
            return reel
        except requests.RequestException as e:
            print(f"Error publishing reel: {e}")
            return None

    def share_public_post(
        self, page_id: str, post_id: str, message: Optional[str] = None
    ) -> Optional[Dict]:
        """Shares a public post from another user on a Facebook Page."""
        try:
            shared_post = self.api_client.put_object(
                page_id,
                "feed",
                link=f"https://www.facebook.com/{post_id}",
                message=message,
            )
            print(f"Post shared successfully. Shared post ID: {shared_post['id']}")
            return shared_post
        except requests.RequestException as e:
            print(f"Error sharing post: {e}")
            return None

    def share_public_reel(
        self, page_id: str, reel_id: str, message: Optional[str] = None
    ) -> Optional[Dict]:
        """Shares a public reel from another user on a Facebook Page's feed."""
        try:
            shared_reel = self.api_client.put_object(
                page_id,
                "feed",
                link=f"https://www.facebook.com/reel/{reel_id}",
                message=message,
            )
            print(f"Reel shared successfully. Shared post ID: {shared_reel['id']}")
            return shared_reel
        except requests.RequestException as e:
            print(f"Error sharing reel: {e}")
            return None

    def share_public_video(
        self, page_id: str, video_id: str, message: Optional[str] = None
    ) -> Optional[Dict]:
        """Shares a public video from another user on a Facebook Page's feed."""
        try:
            shared_video = self.api_client.put_object(
                page_id,
                "feed",
                link=f"https://www.facebook.com/watch/?v={video_id}",
                message=message,
            )
            print(f"Video shared successfully. Shared post ID: {shared_video['id']}")
            return shared_video
        except requests.RequestException as e:
            print(f"Error sharing video: {e}")
            return None

# ... (Other methods for publishing multi-photo and video posts will be added later)