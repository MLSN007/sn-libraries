import instagrapi
from instagrapi.types import Location
from instagrapi.exceptions import (
    ClientError,
    ClientJSONDecodeError,
    ClientConnectionError,
    ClientNotFoundError,
)
import time
import random
import logging


class IgUtils:
    """
    Utility class for Instagram interactions using Instagrapi.
    """

    def __init__(self, client: instagrapi.Client):
        """
        Initialize the IgUtils class with an Instagrapi client.

        Args:
            client: An authenticated Instagrapi client.
        """
        self.client = client

    def get_location_by_pk(self, pk: int, max_retries: int = 3) -> Location | None:
        """
        Get location information by its unique identifier (PK), with retry logic.

        Args:
            pk: The PK of the location.
            max_retries: The maximum number of retry attempts (default: 3).

        Returns:
            The Location object representing the location, or None if not found after retries.
        """
        retries = 0
        while retries < max_retries:
            try:
                return self.client.location_info(pk)
            except (
                ClientError,
                ClientJSONDecodeError,
                ClientConnectionError,
                ClientNotFoundError,
            ) as e:
                if isinstance(e, ClientNotFoundError):
                    return None  # Location not found

                retries += 1
                delay = random.uniform(3, 8)
                time.sleep(delay)
                logging.warning(
                    f"Retrying (attempt {retries}/{max_retries}) after {delay:.2f} seconds due to: {e}"
                )

        logging.error(f"Failed to fetch location after {max_retries} retries.")
        return None

    def get_locations_by_name(
        self, name: str, limit: int = 10, max_retries: int = 3
    ) -> list[Location]:
        """
        Search for locations by name, with retry logic.

        Args:
            name: The name of the location to search for.
            limit: The maximum number of locations to return (default: 10).
            max_retries: The maximum number of retry attempts (default: 3).

        Returns:
            A list of Location objects matching the search query.
        """
        retries = 0
        while retries < max_retries:
            try:
                return self.client.location_search(name, limit=limit)
            except (ClientError, ClientJSONDecodeError, ClientConnectionError) as e:
                retries += 1
                delay = random.uniform(3,8)
                time.sleep(delay)
                logging.warning(
                    f"Retrying (attempt {retries}/{max_retries}) after {delay:.2f} seconds due to: {e}"
                )

        logging.error(f"Failed to search locations after {max_retries} retries.")
        return []

    def get_top_locations_by_name(
        self, name: str, limit: int = 10, max_retries: int = 3
    ) -> list[Location]:
        """
        Get top locations matching the search query.

        Args:
            name: The name of the location to search for.
            limit: The maximum number of locations to return (default: 10).

        Returns:
            A list of Location objects that are top matches for the query.
        """
        return [
            loc
            for loc in self.get_locations_by_name(name, limit, max_retries)
            if loc.category == "City"
        ]

    def location_to_dict(self, location: Location) -> dict:
        """
        Convert a Location object to a dictionary.

        Args:
            location: The Location object to convert.

        Returns:
            A dictionary representation of the location information.
        """
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
