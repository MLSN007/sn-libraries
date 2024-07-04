"""
ig_utils.py:
Provides utility classes and functions for Instagram interactions and data management.
"""

import time
import random
import logging
import pandas as pd
from PIL import Image
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import instagrapi
from instagrapi.types import Location, Usertag, Track
from instagrapi.exceptions import (
    ClientError,
    ClientJSONDecodeError,
    ClientConnectionError,
    ClientNotFoundError,
    UserNotFound
    )
from ig_data import IgPostData


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IgUtils:
    """Utility class for Instagram interactions and data management."""

    MAX_RETRIES = 3
    RETRY_DELAY = 5

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
        self, name: str, max_retries: int = MAX_RETRIES
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


    def music_search(self, query: str) -> List[Track]:
        """Searches for music tracks on Instagram based on a query."""
        try:
            return self.client.search_music(query)
        except ClientError as e:
            logger.error(f"Error searching for music: {e}")
            raise  # Re-raise the exception after logging


    def music_by_author(self, author: str) -> List[Track]:
        """Finds music tracks by a specific author on Instagram."""
        return self.client.search_music(author)


    def get_track_by_id(self, track_pk: str) -> Track | None:
        """Gets a Track object by its ID (pk)."""
        try:
            return self.client.track_info_by_canonical_id(track_pk)
        except ClientError as e:
            logger.error(f"Error fetching track with ID {track_pk}: {e}")
            return None



    def get_user_id_from_username(self, username: str) -> Optional[int]:
        """
        Gets a user's ID from their username.

        Args:
            username (str): The username of the user.

        Returns:
            Optional[int]: The user ID (pk) if found, otherwise None.
        """

        try:
            user_info = self.client.client.user_info_by_username(username)
            return user_info.pk
        except UserNotFound:
            logger.error(f"User '{username}' not found.")
            return None
        except ClientError as e:
            logger.error(f"Error getting user ID for '{username}': {e}")
            return None
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None

# ......................................
# ADITIONAL METHODS
# ......................................


def create_post_dataframe(posts: List[IgPostData]) -> pd.DataFrame:
    """Creates a Pandas DataFrame from a list of IgPostData objects."""
    # Placeholder for future implementation
    pass



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

    ##___________________
    # ### Improve by checking it is a photo file, otherwise return nd continue
    # -------------------------------------------------------------------------------------

    try:
        img = Image.open(image_path)

        # Check if EXIF data exists before trying to access it
        exif_data = img.getexif()

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