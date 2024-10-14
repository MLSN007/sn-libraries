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
import os
import traceback
import random


class FbPostManager:
    """Manages Facebook post-related actions.

    Args:
        api_client (FacebookAPIClient): An instance of the FacebookAPIClient for API interaction.
    """

    def __init__(self, api_client: "FacebookAPIClient") -> None:
        self.api_client = api_client

    def get_latest_posts(
        self, page_id: str, num_posts: int = 10, fields: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
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
                page_id, "posts", fields=fields, limit=num_posts
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

    def publish_text_post(self, page_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Publishes a text-only post on a Facebook Page."""
        try:
            post = self.api_client.put_object(
                page_id, "feed", data={"message": message}
            )
            print(f"Post published successfully. Post ID: {post['id']}")
            return post
        except Exception as e:
            print(f"Error publishing post: {e}")
            return None

    def publish_photo_post(
        self, page_id: str, message: str, photo_path: str
    ) -> Optional[Dict[str, Any]]:
        """Publishes a photo post with a message on a Facebook Page."""
        try:
            with open(photo_path, "rb") as image_file:
                post = self.api_client.put_photo(
                    image=image_file, message=message, album_path=f"{page_id}/photos"
                )
            print(
                f"Post with photo published successfully. Post ID: {post.get('post_id') or post.get('id')}"
            )
            return post
        except Exception as e:
            print(f"Error publishing post with photo: {e}")
            return None

    def _format_post_result(self, post: Dict[str, Any]) -> str:
        """Formats the post result into a friendly string."""
        formatted_result = "Post Details:\n"
        formatted_result += f"  Post ID: {post.get('id', 'N/A')}\n"
        formatted_result += (
            f"  Post URL: https://www.facebook.com/{post.get('id', '')}\n"
        )

        if "message" in post:
            formatted_result += f"  Message: {post['message']}\n"

        if "created_time" in post:
            formatted_result += f"  Created at: {post['created_time']}\n"

        if "attachments" in post:
            formatted_result += "  Attachments:\n"
            for attachment in post["attachments"].get("data", []):
                formatted_result += f"    - Type: {attachment.get('type', 'N/A')}\n"
                if "media" in attachment:
                    formatted_result += f"      URL: {attachment['media'].get('image', {}).get('src', 'N/A')}\n"

        return formatted_result

    def publish_multi_photo_post(
        self, page_id: str, message: str, photo_paths: List[str], max_retries: int = 3
    ) -> Optional[Dict]:
        """Publishes a post with multiple photos to a Facebook Page."""
        try:
            print(f"Attempting to publish multi-photo post to page_id: {page_id}")
            print(f"Message: {message}")
            print(f"Photo paths: {photo_paths}")

            photo_ids = []
            for photo_path in photo_paths:
                retries = 0
                while retries < max_retries:
                    try:
                        print(f"Uploading photo: {photo_path} (Attempt {retries + 1})")
                        with open(photo_path, "rb") as photo_file:
                            photo = self.api_client.put_photo(
                                image=photo_file,
                                message=None,
                                album_path=f"{page_id}/photos",
                                published=False
                            )
                        print(f"Photo upload response: {photo}")
                        photo_ids.append({"media_fbid": photo['id']})
                        break  # Successfully uploaded, break the retry loop
                    except Exception as e:
                        print(f"Error uploading photo: {e}")
                        retries += 1
                        if retries < max_retries:
                            wait_time = random.uniform(1, 5)  # Random wait between 1 and 5 seconds
                            print(f"Retrying in {wait_time:.2f} seconds...")
                            time.sleep(wait_time)
                        else:
                            print(f"Failed to upload photo after {max_retries} attempts")
                            raise

                # Add a delay between photo uploads
                time.sleep(2)

            if not photo_ids:
                raise ValueError("No photos were successfully uploaded")

            print(f"All photos uploaded. Photo IDs: {photo_ids}")

            # Now create the post with all photo IDs
            post_data = {
                "message": message,
                "attached_media": json.dumps(photo_ids)
            }
            print(f"Creating post with data: {post_data}")

            post = self.api_client.put_object(
                page_id,
                "feed",
                **post_data
            )
            print(f"Post creation response: {post}")

            print(f"Multi-photo post published successfully. Post ID: {post.get('id')}")
            return post
        except Exception as e:
            print(f"Error publishing multi-photo post: {e}")
            print("Traceback:")
            traceback.print_exc()
            return None

    def publish_video_post(
        self, page_id: str, message: str, video_path: str, title: Optional[str] = None
    ) -> Optional[Dict]:
        """Publishes a video post to a Facebook Page."""
        try:
            with open(video_path, "rb") as video_file:
                video_data = {
                    "description": message,
                    "title": title if title else "Uploaded video",
                }
                files = {"source": video_file}

                post = self.api_client.put_object(
                    page_id, "videos", data=video_data, files=files
                )
            print(f"Video post published successfully. Post ID: {post.get('id')}")
            return post
        except requests.RequestException as e:
            print(f"Error publishing video post: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response content: {e.response.content}")
            return None
        except Exception as e:
            print(f"Unexpected error publishing video post: {e}")
            return None

    def publish_reel(
        self,
        page_id: str,
        message: str,
        video_path: str,
        title: Optional[str] = None,
        is_reel: bool = True,
    ) -> Optional[Dict]:
        """Publishes reel to a Facebook Page."""
        try:
            with open(video_path, "rb") as video_file:
                video_data = {
                    "description": message,
                    "title": title if title else "Uploaded video",
                }
                if is_reel:
                    video_data["is_reel"] = "true"
                files = {"source": video_file}

                reel = self.api_client.put_object(
                    page_id, "videos", data=video_data, files=files
                )
            print(
                f"Video {'reel' if is_reel else 'post'} published successfully. Post ID: {reel.get('id')}"
            )
            return reel
        except requests.RequestException as e:
            print(f"Error publishing video {'reel' if is_reel else 'post'}: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response content: {e.response.content}")
            return None
        except Exception as e:
            print(
                f"Unexpected error publishing video {'reel' if is_reel else 'post'}: {e}"
            )
            return None

    def _format_reel_result(self, reel: Dict[str, Any]) -> str:
        """Formats the reel result into a friendly string."""
        formatted_result = "Reel Details:\n"
        formatted_result += f"  Reel ID: {reel.get('id', 'N/A')}\n"
        formatted_result += (
            f"  Reel URL: https://www.facebook.com/reel/{reel.get('id', '')}\n"
        )

        if "description" in reel:
            formatted_result += f"  Description: {reel['description']}\n"

        if "title" in reel:
            formatted_result += f"  Title: {reel['title']}\n"

        if "created_time" in reel:
            formatted_result += f"  Created at: {reel['created_time']}\n"

        return formatted_result

    def publish_carousel(
        self, page_id: str, message: str, photo_paths: List[str]
    ) -> Optional[Dict]:
        """Publishes a carousel post to a Facebook Page."""
        # Implementation

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
