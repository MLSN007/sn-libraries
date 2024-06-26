"""
ig_follow_manager.py: Fetches and manages Instagram followings using the HikerAPI and Instagrapi.
"""
import os
import json
import logging
import time
import random
from hikerapi import Client
from ig_client import IgClient
from ig_data import IgPost


class IgFollowManager:
    """A class for managing Instagram followings using both HikerAPI and Instagrapi."""

    def __init__(self, hiker_api_key=os.environ.get("HikerAPI_key"), insta_client: IgClient = None):
        """
        Initializes the IgFollowManager with the HikerAPI key and an optional IgClient instance.

        Args:
            hiker_api_key (str, optional): Your HikerAPI key. Defaults to the value of the environment variable HIKER_API_KEY.
            insta_client (IgClient, optional): An IgClient instance for following actions. If not provided, a new one will be created.
        """
        if not hiker_api_key:
            raise ValueError("HikerAPI_key environment variable not found.")

        self.hiker_client = Client(token=hiker_api_key)
        self.insta_client = insta_client or IgClient()

    def fetch_following(self, user_id=None, username=None, max_results=500):
        """
        Fetches the users that a given user follows.

        Args:
            user_id (int, optional): The Instagram user ID.
            username (str, optional): The Instagram username.
            max_results (int, optional): The maximum number of followings to retrieve. Defaults to 500.

        Returns:
            list: A list of dictionaries containing information about the followed users.
        """
        if not user_id and not username:
            raise ValueError("Either user_id or username must be provided.")

        try:
            # Use user_following_v1 for more details
            following = self.hiker_client.user_following(user_id=user_id, max_requests=max_results)

            # Extract only the desired fields
            extracted_following = []
            for user in following:
                extracted_following.append({
                    "pk": user["pk"],  # or user.get("pk_id") depending on HikerAPI's response
                    "username": user["username"],
                    "full_name": user["full_name"],
                    "is_private": user["is_private"],
                    "is_verified": user["is_verified"],
                    # "account_type": user["account_type"],
                })

            return extracted_following

        except Exception as e:
            logging.error("Error fetching following data: %s", e)
            return []



    def follow_users(self, user_ids, follow_delay=60, max_follows_per_day=50):
        """
        Follows a list of Instagram users with rate limiting and random delay between actions.

        Args:
            user_ids (list): A list of Instagram user IDs to follow.
            follow_delay (int, optional): Base delay in seconds between follow actions. Defaults to 60.
            max_follows_per_day (int, optional): Maximum number of users to follow per day. Defaults to 50.
            
            follow delay is then randomized to better reproduce user behaviour
        """
        followed_count = 0
        for user_id in user_ids:
            if followed_count >= max_follows_per_day:
                logging.info("Reached maximum follows per day limit. Stopping for today.")
                break

            try:
                self.insta_client.client.user_follow(user_id)
                logging.info("Followed user with ID: %s", user_id)
                followed_count += 1

                # Calculate random delay
                min_delay = follow_delay - follow_delay / 5
                max_delay = follow_delay + follow_delay / 3
                random_delay = random.uniform(min_delay, max_delay)
                
                logging.info(f"Waiting for {random_delay:.2f} seconds before next follow...")
                time.sleep(random_delay)  # Sleep for the random duration

            except Exception as e:
                logging.error("Error following user with ID %s: %s", user_id, e)


    def save_following_data(self, following_data, username, output_file=None):
        """
        Saves the following data to a JSON file with a structured filename.

        Args:
            following_data (list): The list of following dictionaries.
            username (str): The username whose followings are being saved.
            output_file (str, optional): The path to the output JSON file. If not provided, a filename based on username and data length will be generated.
        """
        if not output_file:
            output_file = f"{username}_following_{len(following_data)}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(following_data, f, ensure_ascii=False, indent=4)
        logging.info("Saved following data to %s", output_file)

