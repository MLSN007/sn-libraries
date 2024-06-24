"""
ig_data.py:
Handles data related to Instagram posts, including storage in a Pandas DataFrame.
"""

import pandas as pd
from datetime import datetime

class IgPost:
    """Represents an Instagram post with relevant data."""

    def __init__(self, media_id, media_type, caption, timestamp, location, like_count, comment_count):
        self.media_id = media_id
        self.media_type = media_type
        self.caption = caption
        self.timestamp = timestamp  # Should be a datetime object
        self.location = location  # Can be None if no location is tagged
        self.like_count = like_count
        self.comment_count = comment_count


def create_post_dataframe(posts):
    """
    Creates a Pandas DataFrame from a list of IgPost objects.
    """
    data = [
        {
            "Media ID": post.media_id,
            "Type": post.media_type,
            "Caption": post.caption,
            "Timestamp": post.timestamp,
            "Location": post.location.name if post.location else None,
            "Likes": post.like_count,
            "Comments": post.comment_count,
        }
        for post in posts
    ]

    return pd.DataFrame(data)

