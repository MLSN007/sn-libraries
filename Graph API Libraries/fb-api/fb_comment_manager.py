"""CommentManager class for handling Facebook comment actions."""


from typing import List, Dict, Any, Optional
import facebook  # Make sure you have the 'facebook-sdk' library installed
import requests

class FbCommentManager:
    """Manages Facebook comment-related actions."""

    def __init__(self, api_client: "FbApiClient") -> None:
        self.api_client = api_client

    def get_post_comments(
        self, post_id: str, fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves comments for a specific Facebook post.

        Args:
            post_id (str): The ID of the post.
            fields (Optional[List[str]]): List of comment fields to include.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
                                 represents a comment.
        """

        graph = self.api_client.get_graph_api_object()
        all_comments = []
        default_fields = ["id", "message", "created_time", "from", "like_count", "parent", "user_likes","reactions"]  # Updated default fields
        fields_str = ",".join(fields or default_fields)

        try:
            comments = graph.get_connections(
                id=post_id, connection_name="comments", fields=fields_str
            )

            all_comments.extend(comments["data"])

            # Handle paging with timeout
            while "paging" in comments and "next" in comments["paging"]:
                next_url = comments["paging"]["next"]
                comments = requests.get(next_url, timeout=10).json()  # 10-second timeout
                all_comments.extend(comments["data"])

        except requests.Timeout: 
            print(f"Request timed out while fetching comments for post {post_id}")
            return all_comments

        except facebook.GraphAPIError as e:
            print(f"Error retrieving comments: {e}")
            return []  # Return empty list on error

        return all_comments


    def react_to_comment(
        self, comment_id: str, message: Optional[str] = None, like: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Reacts to a comment by replying and/or liking it.

        Args:
            comment_id (str): The ID of the comment to react to.
            message (Optional[str]): The reply message. If None, no reply is posted.
            like (bool, optional): Whether to like the comment. Defaults to False.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the API response if successful,
                                      or None if an error occurs.
        """

        graph = self.api_client.get_graph_api_object()
        response = None  # Initialize response variable

        try:
            if message:
                # Reply to the comment
                response = graph.put_comment(object_id=comment_id, message=message)
                print(f"Replied to comment {comment_id}: {message}")

            if like:
                # Like the comment
                response = graph.put_like(object_id=comment_id)
                print(f"Liked comment {comment_id}")

        except facebook.GraphAPIError as e:
            print(f"Error reacting to comment: {e}")

        return response  # Return the API response, if any
