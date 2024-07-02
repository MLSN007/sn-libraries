"""
Instagram Story Manager
Module string
"""

from typing import List, Union, Optional
from pathlib import Path
import logging
from instagrapi import Client
from instagrapi.types import StoryBuild, StoryLink, StoryMention, StoryHashtag, StorySticker
from ig_data import IgStData

#Get the logger
logger = logging.getLogger(__name__)

class IgStManager:
    """
    Class to manage Instagram Story interactions.
    """

    def __init__(self, client: Client):
        """Initialize with an authenticated Instagrapi client."""
        self.client = client

    def upload_story_photo(
        self, photo_path: Path, mentions: List[StoryMention] = [],
        hashtags: List[StoryHashtag] = [], links: List[StoryLink] = [],
        stickers: List[StorySticker] = [], captions: List[str] = []) -> None:
        """
        Uploads a photo as an Instagram Story.

        Args:
            photo_path: Path to the photo file.
            mentions: List of StoryMention objects.
            hashtags: List of StoryHashtag objects.
            links: List of StoryLink objects.
            stickers: List of StorySticker objects.
            captions: List of captions for each photo (if multiple photos are uploaded).

        Returns:
            None
        """
        story = self.client.photo_upload_to_story(
            photo_path, mentions=mentions, hashtags=hashtags, links=links, stickers=stickers, captions=captions
        )
        logger.info(f"Story photo uploaded: {story}")
        st_data = IgStData(
            media_id=story_item.id,
            media_type=story_item.media_type,
            caption=captions[0] if captions else "",
            timestamp=story_item.taken_at,  # Or whatever time you want to record
            media_url=story_item.thumbnail_url  # If applicable for this story type
        )
        print(st_data)

    # Add methods for uploading videos, creating text stories, adding filters, etc.
