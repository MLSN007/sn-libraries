"""A class for managing Facebook comment-related actions."""

import requests
from typing import List, Dict, Any, Optional


class FbCommentManager:
    """A class for managing Facebook comment-related actions.

    This class provides methods for retrieving comments for Facebook posts, reacting
    to comments (by replying and liking), and potentially more comment-related
    functionality in the future.

    Args:
        api_client (FbApiClient): An instance of the FbApiClient for handling
            Facebook Graph API interactions.
    """

    def __init__(self, api_client: "FbApiClient") -> None:
        self.api_client = api_client

    def get_post_comments(
        self, post_id: str, fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves comments for a specific Facebook post with optional filtering.

        Args:
            post_id (str): The ID of the post.
            fields (Optional[List[str]]): List of comment fields to include (e.g.,
                ['id', 'message', 'from']). If None, default fields are used.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a comment,
                including the requested fields. Empty list if an error occurs.
        """

        default_fields = [
            "id",
            "message",
            "created_time",
            "from",
            "like_count",
            "parent",
            "user_likes",
            "reactions",
        ]
        fields_str = ",".join(fields or default_fields)

        try:
            comments = self.api_client.get_connections(
                post_id, "comments", fields=fields_str
            )
            all_comments = comments.get("data", [])

            while "paging" in comments and "next" in comments["paging"]:
                next_url = comments["paging"]["next"]
                comments = requests.get(next_url, timeout=10).json()
                all_comments.extend(comments.get("data", []))

            return all_comments
        except requests.RequestException as e:
            print(f"Error retrieving comments: {e}")
            return []

    def react_to_comment(
        self, comment_id: str, message: Optional[str] = None, like: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Reacts to a Facebook comment by replying (optional) and liking (optional).

        Args:
            comment_id (str): The ID of the comment.
            message (Optional[str]): The reply message. If None, no reply is sent.
            like (bool, optional): Whether to like the comment (default: False).

        Returns:
            Optional[Dict[str, Any]]: The API response from posting the reply or like
                (if successful), or None if an error occurs.
        """

        try:
            response = None
            if message:
                response = self.api_client.put_object(
                    comment_id, "comments", message=message
                )
                print(f"Replied to comment {comment_id}: {message}")

            if like:
                response = self.api_client.put_object(comment_id, "likes")
                print(f"Liked comment {comment_id}")

        except requests.RequestException as e:
            print(f"Error reacting to comment: {e}")

        return response  # Return the API response, if any
