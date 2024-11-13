"""A class for managing Facebook comment-related actions."""

import requests
from typing import List, Dict, Any, Optional

from .fb_api_client import FbApiClient


class FbCommentManager:
    """A class for managing Facebook comment-related actions.

    This class provides methods for retrieving comments for Facebook posts, reacting
    to comments (by replying and liking), and posting new comments.

    Args:
        api_client (FbApiClient): An instance of the FbApiClient for handling
            Facebook Graph API interactions.
    """

    def __init__(self, api_client: FbApiClient) -> None:
        self.api_client = api_client

    def get_post_comments(
        self, post_id: str, fields: Optional[List[str]] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieves comments for a specific Facebook post with optional filtering.

        Args:
            post_id (str): The ID of the post.
            fields (Optional[List[str]]): List of comment fields to include (e.g.,
                ['id', 'message', 'from']). If None, default fields are used.
            limit (int): Maximum number of comments to retrieve (default: 100).

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
                post_id, "comments", fields=fields_str, limit=limit
            )
            all_comments = comments.get("data", [])

            while "paging" in comments and "next" in comments["paging"] and len(all_comments) < limit:
                next_url = comments["paging"]["next"]
                comments = requests.get(next_url, timeout=10).json()
                all_comments.extend(comments.get("data", []))
                if len(all_comments) > limit:
                    all_comments = all_comments[:limit]

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

            return response
        except requests.RequestException as e:
            print(f"Error reacting to comment: {e}")
            return None

    def post_comment(self, post_id: str, message: str) -> Optional[Dict[str, Any]]:
        """Posts a new comment on a Facebook post."""
        try:
            response = self.api_client.put_object(post_id, "comments", message=message)
            print(f"Posted comment on post {post_id}: {message}")
            return response
        except Exception as e:
            print(f"Error posting comment: {e}")
            if hasattr(e, 'response'):
                print(f"Response content: {e.response.content}")
            return None

    def get_comment_replies(
        self, comment_id: str, fields: Optional[List[str]] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieves replies to a specific comment.

        Args:
            comment_id (str): The ID of the parent comment.
            fields (Optional[List[str]]): List of reply fields to include. If None, default fields are used.
            limit (int): Maximum number of replies to retrieve (default: 100).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a reply,
                including the requested fields. Empty list if an error occurs.
        """
        default_fields = [
            "id",
            "message",
            "created_time",
            "from",
            "like_count",
            "user_likes",
        ]
        fields_str = ",".join(fields or default_fields)

        try:
            replies = self.api_client.get_connections(
                comment_id, "comments", fields=fields_str, limit=limit
            )
            all_replies = replies.get("data", [])

            while "paging" in replies and "next" in replies["paging"] and len(all_replies) < limit:
                next_url = replies["paging"]["next"]
                replies = requests.get(next_url, timeout=10).json()
                all_replies.extend(replies.get("data", []))
                if len(all_replies) > limit:
                    all_replies = all_replies[:limit]

            return all_replies
        except requests.RequestException as e:
            print(f"Error retrieving comment replies: {e}")
            return []

    def get_comment_reactions(self, comment_id: str) -> Dict[str, int]:
        """Retrieves detailed reaction information for a specific comment.

        Args:
            comment_id (str): The ID of the comment.

        Returns:
            Dict[str, int]: A dictionary containing reaction types and their counts.
        """
        try:
            reaction_types = ["LIKE", "LOVE", "WOW", "HAHA", "SAD", "ANGRY", "THANKFUL"]
            reactions = {}

            for reaction_type in reaction_types:
                response = self.api_client.get_connections(
                    comment_id, "reactions", type=reaction_type
                )
                reactions[reaction_type.lower()] = len(response.get("data", []))

            return reactions
        except requests.RequestException as e:
            print(f"Error retrieving comment reactions: {e}")
            return {}
