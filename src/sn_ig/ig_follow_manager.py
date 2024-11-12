"""Fetches and manages Instagram followings using the HikerAPI and Instagrapi.

This module provides a class, `IgFollowManager`, for retrieving and managing
Instagram following data. It utilizes both the HikerAPI for fetching following
information and Instagrapi for performing follow actions.
"""

import os
import json
import logging
import time
import random
from typing import List, Dict, Optional
from hikerapi import Client
from ig_client import IgClient

MAX_RESULTS = 500
MAX_FOLLOWS_PER_DAY = 50
BASE_FOLLOW_DELAY = 60


class IgFollowManager:
    """A class for managing Instagram followings using the HikerAPI and Instagrapi.

    Attributes:
        hiker_client (Client): An instance of the HikerAPI client.
        insta_client (IgClient): An instance of the IgClient.

    Args:
        hiker_api_key (str, optional): Your HikerAPI key. Defaults to the value of the environment variable "HikerAPI_key".
        insta_client (IgClient, optional): An IgClient instance. If not provided, a new instance is created.

    Raises:
        ValueError: If the "HikerAPI_key" environment variable is not set.
    """

    def __init__(self, hiker_api_key: Optional[str] = os.environ.get("HikerAPI_key"), insta_client: Optional[IgClient] = None) -> None:
        if not hiker_api_key:
            raise ValueError("HikerAPI_key environment variable not found.")

        self.hiker_client = Client(token=hiker_api_key)
        self.insta_client = insta_client or IgClient()

    def fetch_following(self, user_id: Optional[int] = None, username: Optional[str] = None, max_results: int = MAX_RESULTS) -> List[Dict]:
        """Fetches the users that a given user is following.

        Args:
            user_id (int, optional): The Instagram user ID.
            username (str, optional): The Instagram username.
            max_results (int, optional): The maximum number of results to fetch (default: 500).

        Returns:
            List[Dict]: A list of dictionaries containing information about each followed user.
                Each dictionary has the following keys: "pk", "username", "full_name", "is_private", and "is_verified".

        Raises:
            ValueError: If neither `user_id` nor `username` is provided.
            Exception: For any other unexpected errors during data fetching.
        """
        if not user_id and not username:
            raise ValueError("Either user_id or username must be provided.")

        try:
            following = self.hiker_client.user_following(user_id=user_id, max_requests=max_results)

            extracted_following = [
                {
                    "pk": user["pk"],
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "is_private": user["is_private"],
                    "is_verified": user["is_verified"],
                }
                for user in following
            ]

            return extracted_following

        except Exception as e:
            logger.error("Error fetching following data: %s", e)
            return []

    def follow_users(self, user_ids: List[int], follow_delay: int = BASE_FOLLOW_DELAY, max_follows_per_day: int = MAX_FOLLOWS_PER_DAY) -> None:
        """Follows a list of Instagram users, respecting daily limits and delays.

        Args:
            user_ids (List[int]): A list of Instagram user IDs to follow.
            follow_delay (int, optional): The base delay between follow actions in seconds (default: 60).
            max_follows_per_day (int, optional): The maximum number of follows allowed per day (default: 50).
        """
        followed_count = 0
        for user_id in user_ids:
            if followed_count >= max_follows_per_day:
                logger.info("Reached maximum follows per day limit. Stopping for today.")
                break

            try:
                self.insta_client.client.user_follow(user_id)
                logger.info("Followed user with ID: %s", user_id)
                followed_count += 1

                random_delay = random.uniform(follow_delay * 0.8, follow_delay * 1.3)
                logger.info("Waiting for %.2f seconds before next follow...", random_delay)
                time.sleep(random_delay)

            except Exception as e:
                logger.error("Error following user with ID %s: %s", user_id, e)

    def save_following_data(self, following_data: List[Dict], username: str, output_file: Optional[str] = None) -> None:
        """Saves the following data to a JSON file.

        Args:
            following_data (List[Dict]): The following data to be saved.
            username (str): The username associated with the following data.
            output_file (str, optional): The path to the output JSON file. If not provided, a default filename will be generated based on the username and number of entries in `following_data`.
        """
        if not output_file:
            output_file = f"{username}_following_{len(following_data)}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(following_data, f, ensure_ascii=False, indent=4)
        logger.info("Saved following data to %s", output_file)