from typing import Dict, Optional
import facebook

class PostManager:
    """Manages Facebook post-related actions.

    Args:
        api_client (FacebookAPIClient): An instance of the FacebookAPIClient for API interaction.
    """

    def __init__(self, api_client: "FacebookAPIClient") -> None:
        self.api_client = api_client

    def publish_text_post(self, page_id: str, message: str) -> Optional[Dict]:
        """Publishes a text-only post on the specified Facebook Page.

        Args:
            page_id (str): The ID of the page to publish the post on.
            message (str): The text content of the post.

        Returns:
            Optional[Dict]: A dictionary containing post details if successful,
            or None if an error occurs.
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
        """Publishes a post with a photo and text on the specified Facebook Page.

        Args:
            page_id (str): The ID of the page to publish the post on.
            message (str): The text content of the post.
            photo_path (str): The path to the photo file.

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
