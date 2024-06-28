"""
ig_data.py:
Handles data related to Instagram posts, including storage in a Pandas DataFrame.
"""

import pandas as pd
from datetime import datetime
import logging
from typing import List, Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IgPost:
    """Represents an Instagram post with relevant data."""

    def __init__(self, media_id: Optional[str] = None, media_type: Optional[str] = None, 
                 caption: Optional[str] = None, timestamp: Optional[datetime] = None,
                 location: Optional[str] = None, like_count: Optional[int] = None, 
                 comment_count: Optional[int] = None, published: bool = False, 
                 failed_attempts: int = 0, last_failed_attempt: Optional[datetime] = None,
                 tags: Optional[List[str]] = None, mentions: Optional[List[str]] = None) -> None:
        
        self.media_id = media_id
        self.media_type = media_type
        self.caption = caption
        self.timestamp = timestamp
        self.location = location
        self.like_count = like_count
        self.comment_count = comment_count
        self.published = published
        self.failed_attempts = failed_attempts
        self.last_failed_attempt = last_failed_attempt
        self.tags = tags or []
        self.mentions = mentions or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert the IgPost instance to a dictionary."""
        return {
            'media_id': self.media_id,
            'media_type': self.media_type,
            'caption': self.caption,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'location': self.location,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'published': self.published,
            'tags': self.tags,
            'mentions': self.mentions,
            'failed_attempts': self.failed_attempts,
            'last_failed_attempt': self.last_failed_attempt.isoformat() if self.last_failed_attempt else None 
        }

def create_post_dataframe(posts: List[IgPost]) -> pd.DataFrame:
    """
    Creates a Pandas DataFrame from a list of IgPost objects.

    Args:
        posts (List[IgPost]): A list of IgPost objects.

    Returns:
        pd.DataFrame: A DataFrame containing the post data.
    """
    data = [
        {
            "Media ID": post.media_id,
            "Type": post.media_type,
            "Caption": post.caption,
            "Timestamp": post.timestamp,
            "Location": post.location,
            "Likes": post.like_count,
            "Comments": post.comment_count,
            "Published": post.published,
            "Tags": ", ".join(post.tags),
            "Mentions": ", ".join(post.mentions),
            "Failed Attempts": post.failed_attempts,
            "Last Failed Attempt": post.last_failed_attempt.strftime('%Y-%m-%d %H:%M:%S') if post.last_failed_attempt else None,
        }
        for post in posts
    ]

    return pd.DataFrame(data)

def save_post_dataframe(df: pd.DataFrame, filename: str = "ig_posts.csv") -> None:
    """
    Saves the DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        filename (str, optional): The name of the file to save the DataFrame to. Defaults to "ig_posts.csv".

    Raises:
        IOError: If there's an error saving the DataFrame to the file.
    """
    try:
        df.to_csv(filename, index=False)
        logger.info(f"DataFrame saved to {filename}")
    except IOError as e:
        logger.error(f"Error saving DataFrame: {e}")
        raise