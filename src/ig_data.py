"""
ig_data.py:
Handles data related to Instagram posts, including storage in a Pandas DataFrame.
"""

import pandas as pd
from datetime import datetime

class IgPost:
    """Represents an Instagram post with relevant data."""

    def __init__(self, media_id=None, media_type=None, caption=None, timestamp=None,
                 location=None, like_count=None, comment_count=None,
                 published=False, failed_attemps = 0,
                 last_failed_attempt=None,
                 tags=None, mentions=None):
        
        self.media_id = media_id
        self.media_type = media_type
        self.caption = caption
        self.timestamp = timestamp  # Should be a datetime object
        self.location = location  # Can be None if no location is tagged
        self.like_count = like_count
        self.comment_count = comment_count
        self.published = published          # Whether the post was successfully published
        self.failed_attempts = failed_attemps
        self.last_failed_attempt = last_failed_attempt    # Timestamp of the last failed attempt (if any)
        self.tags = tags or []  # Use an empty list as the default if tags is None
        self.mentions = mentions or []  # Use an empty list as the default if mentions is None


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
            "Published": post.published,
            "Tags": ", ".join(post.tags), # Assuming post.tags is a list of strings
            "Mentions": ", ".join(post.mentions),   # Assuming post.mentions is a list of strings
            "Failed Attempts": post.failed_attempts,  # Correct attribute name
            "Last Failed Attempt": post.last_failed_attempt.strftime('%Y-%m-%d %H:%M:%S') if post.last_failed_attempt else None,
        }
        for post in posts
    ]

    return pd.DataFrame(data)


def save_post_dataframe(df, filename="ig_posts.csv"):
    """Saves the DataFrame to a CSV file."""
    try:
        df.to_csv(filename, index=False)  # Save without row indices
        print(f"DataFrame saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving DataFrame: {e}")
        raise
