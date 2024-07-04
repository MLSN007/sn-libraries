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
import facebook

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

        graph = self.api_client.get_graph_api_object()

        # Define default fields if none are provided
        default_fields = ("id,message,created_time,permalink_url,"
                        "likes.summary(true),comments.summary(true)")
        fields = fields or default_fields

        try:
            posts = graph.get_connections(
                id=page_id, connection_name="posts", fields=fields, limit=num_posts
            )
            return posts["data"]
        except facebook.GraphAPIError as e:
            print(f"Error retrieving latest posts: {e.message}")
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

        graph = self.api_client.get_graph_api_object()
        fields = ("id,message,created_time,permalink_url,"
                  "likes.summary(true),comments.summary(true),attachments")

        try:
            post_data = graph.get_object(id=post_id, fields=fields)

            # Process attachments (if present)
            if "attachments" in post_data:
                attachments = post_data["attachments"]["data"]
                for attachment in attachments:
                    if attachment.get("media_type") == "photo":
                        # Access photo URL from attachment['media']['image']['src']
                        photo_url = attachment['media']['image']['src']
                        print(f"Found photo: {photo_url}")
                    elif attachment.get("media_type") == "video":
                        # Access video URL from attachment['media']['source']
                        video_url = attachment['media']['source']
                        print(f"Found video: {video_url}")

            return post_data

        except facebook.GraphAPIError as e:
            print(f"Error retrieving post by ID: {e.message}")
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
        graph = self.api_client.get_graph_api_object()
        likes = []

        try:
            likes_response = graph.get_connections(
                id=post_id,
                connection_name="likes",
                # No need for specific fields as we handle permissions below
            )
            likes_data = likes_response.get("data", [])

            for like_data in likes_data:
                if "name" in like_data and "id" in like_data:
                    likes.append(like_data)  # If name and ID available, add as is
                else:
                    likes.append({"unknown": True})  # Add indicator for unknown user

        except facebook.GraphAPIError as e:
            print(f"Error retrieving likes for post {post_id}: {e}")

        return likes


    def get_post_shares(self, post_id: str) -> List[Dict]:
        """Retrieves shared post data for a specific Facebook post.

        Args:
            post_id (str): The ID of the post.

        Returns:
            List[Dict]: A list of dictionaries, each representing a shared post. Returns 0 on error.
        """

        graph = self.api_client.get_graph_api_object()

        try:
            shared_posts = graph.get_all_connections(
                id=post_id,
                connection_name="sharedposts",
            )
            return list(shared_posts)  # Convert generator to a list for easy access

        except facebook.GraphAPIError as e:
            print(f"Error retrieving shares for post {post_id}: {e}")
            return 0  # Return 0 on error


    def publish_text_post(self, page_id: str, message: str) -> Optional[Dict]:
        """Publishes a text-only (or photo) post on a Facebook Page.

        Args:
            page_id (str): The ID of the page to publish the post on.
            message (str): The text content of the post.
            photo_path (str, optional): The path to the photo file (for publish_photo_post only).

        Returns:
            Optional[Dict]: A dictionary containing post details if successful, or None if an error occurs.
        """
        
        graph = self.api_client.get_graph_api_object()
        try:
            post = graph.put_object(
                parent_object=page_id,
                connection_name="feed",
                message=message
            )
            print(f"Post published successfully. Post ID: {post['id']}")
            return post  # Return post data
        except facebook.GraphAPIError as e:
            print(f"Error publishing post: {e.message}")
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
        graph = self.api_client.get_graph_api_object()
        with open(photo_path, "rb") as image_file:
            try:
                post = graph.put_photo(
                    parent_object=page_id,
                    connection_name="photos",
                    message=message,
                    image=image_file,
                )
                print(f"Post with photo published successfully. Post ID: {post['post_id']}")
                return post  # Return post data
            except facebook.GraphAPIError as e:
                print(f"Error publishing post with photo: {e.message}")
                return None

# ... (Other methods for publishing multi-photo and video posts will be added later)
