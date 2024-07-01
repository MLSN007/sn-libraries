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
from instagrapi.types import (
    Media, Location, UserShort, Usertag, Track
)
import instagrapi
from instagrapi.mixins.media import MediaMixin

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
        media_id: str,
        media_type: int,
        caption: str,
        timestamp: datetime,
        media_url: str,
        location: Optional[Location] = None,
        like_count: int = 0,
        comment_count: int = 0,
        usertags: List[Usertag] = None,
        published: bool = True,
        failed_attempts: int = 0,
        last_failed_attempt: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        mentions: Optional[List[str]] = None,
    ) -> None:

        self.media_id = media_id
        self.media_type = media_type
        self.caption = caption
        self.timestamp = timestamp
        self.location = location
        self.media_url = media_url
        self.like_count = like_count
        self.comment_count = comment_count
        self.usertags = usertags or []
        self.published = published
        self.failed_attempts = failed_attempts
        self.last_failed_attempt = last_failed_attempt
        self.tags = tags or []
        self.mentions = mentions or []

    def to_dict(self) -> Dict[str, Any]:
        """Converts the IgPost instance to a JSON-serializable dictionary."""
        data = self.__dict__.copy()
        if self.location:
            data["location"] = IgUtils(self.client).location_to_dict(self.location)
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

        # Check if EXIF data exists before trying to access it
        exif_data = img._getexif()  
        if exif_data and 0x0112 in exif_data:  # 0x0112 is the EXIF tag for orientation
            orientation = exif_data[0x0112]
            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
            img.save(image_path)  
        else:
            logging.warning(f"No EXIF orientation data found in image: {image_path}") 
    except (IOError, OSError) as e:
        logging.error(f"Error opening or processing image: {image_path}, Error: {e}")