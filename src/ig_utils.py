"""
ig_utils.py:
Provides utility classes and functions for Instagram interactions and data management.
"""

import time
import random
import logging
import instagrapi
import pandas as pd
from PIL import Image
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path  # Added for file paths
from instagrapi.types import Media, Location, Usertag, Track
from instagrapi.exceptions import (
    ClientError,
    ClientJSONDecodeError,
    ClientConnectionError,
    ClientNotFoundError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IgPost:
    """Represents an Instagram post with relevant data."""

    def __init__(
        self,
        media: Media,
        location: Optional[Location] = None,
        tags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
    ) -> None:
        """
        Initializes an IgPost object from an Instagrapi Media object.

        Args:
            media: The Media object representing the Instagram post.
            location: The location of the post (optional).
            tags: A list of tags associated with the post (optional).
            mentions: A list of user mentions in the post (optional).
        """

        self.media_id = media.id
        self.media_type = media.media_type
        self.caption = media.caption_text
        self.timestamp = media.taken_at  # Already a datetime object
        self.location = location
        self.media_url = media.thumbnail_url  # Or pick the best media url from media.resources
        self.like_count = media.like_count
        self.comment_count = media.comment_count
        self.usertags = media.usertags or []
        self._media_dict = media.dict()

        self.published = True 
        self.failed_attempts = 0
        self.last_failed_attempt = None
        self.tags = tags or []
        self.mentions = mentions or []

    def to_dict(self) -> Dict[str, Any]:
        """Converts the IgPost instance to a JSON-serializable dictionary."""
        data = self.__dict__.copy()
        del data["_media_dict"]  
        data["media"] = self._media_dict
        return data


class IgUtils:
    """Utility class for Instagram interactions and data management."""

    def __init__(self, client: instagrapi.Client):
        """Initialize with an authenticated Instagrapi client."""
        self.client = client

    def get_location_by_pk(self, pk: int, max_retries: int = 3) -> Location | None:
        """Gets a location by its ID (pk) with retry logic."""
        retries = 0
        while retries < max_retries:
            try:
                return self.client.client.location_info(pk)  # Access underlying client
            except (ClientError, ClientJSONDecodeError, ClientConnectionError, ClientNotFoundError) as e:
                if isinstance(e, ClientNotFoundError):
                    return None  # Location not found

                retries += 1
                delay = random.uniform(3, 8)  # Increased random delay
                time.sleep(delay)
                logger.warning(f"Retrying location fetch (attempt {retries}/{max_retries}) after {delay:.2f}s due to: {e}")
        logger.error(f"Failed to fetch location after {max_retries} retries.")
        return None

    def get_locations_by_name(
        self, name: str, max_retries: int = 3
    ) -> list[Location]:
        """Searches for locations by name with retry logic."""
        retries = 0
        while retries < max_retries:
            try:
                return self.client.client.fbsearch_places(name)
            except (ClientError, ClientJSONDecodeError, ClientConnectionError) as e:
                retries += 1
                delay = random.uniform(3, 8)  # Increased random delay
                time.sleep(delay)
                logging.warning(f"Retrying location search (attempt {retries}/{max_retries}) after {delay:.2f}s due to: {e}")
        logger.error(f"Failed to search locations after {max_retries} retries.")
        return []


    def get_top_locations_by_name(self, name: str, limit: int = 10, max_retries: int = 3) -> list[Location]:
        """Gets the top matching locations for a query."""
        locations = self.get_locations_by_name(name, max_retries)
        return locations[:limit]  


    def location_to_dict(self, location: Location) -> dict:
        """Converts a Location object to a dictionary."""
        return {
            "pk": location.pk,
            "name": location.name,
            "address": location.address,
            "lng": location.lng,
            "lat": location.lat,
            "external_id": location.external_id,
            "external_id_source": location.external_id_source,
            "city": location.city,
            "zip": location.zip,
            "category": location.category,
            "phone": location.phone,
            "website": location.website,
        }


    def search_music(self, query: str) -> List[Track]:
        """Searches for music tracks on Instagram based on a query."""
        try:
            return self.music_search(query)
        except ClientError as e:
            logger.error(f"Error searching for music: {e}")
            raise  # Re-raise the exception after logging


    def music_by_author(self, author: str) -> List[Track]:
        """Finds music tracks by a specific author on Instagram."""
        return self.search_music(author)


    def get_track_by_id(self, track_pk: str) -> Track | None: 
        """Gets a Track object by its ID (pk)."""
        try:
            return self.track_info_by_canonical_id(track_pk)
        except ClientError as e:
            logger.error(f"Error fetching track with ID {track_pk}: {e}")
            return None

def create_post_dataframe(posts: List[IgPost]) -> pd.DataFrame:
    """Creates a Pandas DataFrame from a list of IgPost objects."""
    data = [post.to_dict() for post in posts]
    return pd.DataFrame(data)


def save_post_dataframe(df: pd.DataFrame, filename: str = "ig_posts.csv") -> None:
    """Saves the DataFrame to a CSV file."""
    try:
        df.to_csv(filename, index=False)
        logger.info(f"DataFrame saved to {filename}")
    except IOError as e:
        logger.error(f"Error saving DataFrame: {e}")
        raise


def correct_orientation(image_path: Path) -> None:
    """
    Corrects the orientation of an image based on EXIF data.

    Args:
        image_path: The path to the image file.
    """

    try:
        img = Image.open(image_path)
        exif_orientation_tag = 0x0112
        if hasattr(img, "_getexif") and exif_orientation_tag in img._getexif():
            orientation = img._getexif()[exif_orientation_tag]
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
            img.save(image_path)
    except (AttributeError, KeyError, IndexError):
        # Handle cases where the image doesn't have EXIF data
        pass

