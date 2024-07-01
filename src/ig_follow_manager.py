"""
ig_follow_manager.py: Fetches and manages Instagram followings using the HikerAPI and Instagrapi.
"""
import os
import json
import logging
import time
import random
from typing import List, Dict, Optional
from hikerapi import Client
from ig_client import IgClient
from ig_data_tools import IgPost

MAX_RESULTS = 500
MAX_FOLLOWS_PER_DAY = 50
BASE_FOLLOW_DELAY = 60

class IgFollowManager:
    """A class for managing Instagram followings using both HikerAPI and Instagrapi."""

    def __init__(self, hiker_api_key: Optional[str] = os.environ.get("HikerAPI_key"), insta_client: Optional[IgClient] = None) -> None:
        if not hiker_api_key:
            raise ValueError("HikerAPI_key environment variable not found.")

        self.hiker_client = Client(token=hiker_api_key)
        self.insta_client = insta_client or IgClient()

    def fetch_following(self, user_id: Optional[int] = None, username: Optional[str] = None, max_results: int = MAX_RESULTS) -> List[Dict]:
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
            logging.error("Error fetching following data: %s", e)
            return []

    def follow_users(self, user_ids: List[int], follow_delay: int = BASE_FOLLOW_DELAY, max_follows_per_day: int = MAX_FOLLOWS_PER_DAY) -> None:
        followed_count = 0
        for user_id in user_ids:
            if followed_count >= max_follows_per_day:
                logging.info("Reached maximum follows per day limit. Stopping for today.")
                break

            try:
                self.insta_client.client.user_follow(user_id)
                logging.info("Followed user with ID: %s", user_id)
                followed_count += 1

                random_delay = random.uniform(follow_delay * 0.8, follow_delay * 1.3)
                logging.info(f"Waiting for {random_delay:.2f} seconds before next follow...")
                time.sleep(random_delay)

            except Exception as e:
                logging.error("Error following user with ID %s: %s", user_id, e)

    def save_following_data(self, following_data: List[Dict], username: str, output_file: Optional[str] = None) -> None:
        if not output_file:
            output_file = f"{username}_following_{len(following_data)}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(following_data, f, ensure_ascii=False, indent=4)
        logging.info("Saved following data to %s", output_file)