"""
ig_info_analyzer.py: Extracts and analyzes Instagram user information from a JSON file.
"""
import json
import logging
from typing import List, Dict, Any
import pandas as pd

DEFAULT_INPUT_FILE = "instagram_info.json"
DEFAULT_OUTPUT_FILE = "instagram_profiles.csv"

class IgInfoAnalyzer:
    """A class for extracting and analyzing Instagram user information."""

    def extract_info_data_from_json(self, input_file: str = DEFAULT_INPUT_FILE) -> pd.DataFrame:
        """
        Loads Instagram user information from a JSON file
        and extracts relevant fields into a Pandas DataFrame.

        Args:
            input_file (str, optional): The path to the input JSON file.
                Defaults to "instagram_info.json".

        Returns:
            pandas.DataFrame: A DataFrame containing the extracted user information.

        Raises:
            FileNotFoundError: If the input file is not found.
            json.JSONDecodeError: If the JSON file is invalid.
            KeyError: If expected keys are missing in the JSON data.
        """
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                all_info_data: List[Dict[str, Any]] = json.load(f)

            extracted_data: List[Dict[str, Any]] = []
            for profile in all_info_data:
                if profile["status"] == "ok":
                    user = profile["user"]
                    extracted_data.append({
                        "username": user["username"],
                        "full_name": user["full_name"],
                        "instagram_id": user.get("pk", user.get("pk_id")),
                        "category": user["category"],
                        "biography": user["biography"],
                        "followers": user["follower_count"],
                        "following": user["following_count"],
                        "is_private": user["is_private"],
                        "is_business": user["is_business"],
                        "is_verified": user["is_verified"],
                        "media_count": user["media_count"],
                        "fb_page_id": str(user["page_id"]),
                        "fb_page_name": user["page_name"],
                        "profile_pic_url": user["profile_pic_url"],
                        "external_url": user.get("external_url"),
                        "bio_links": [link["url"] for link in user.get("bio_links", [])],
                    })

            return pd.DataFrame(extracted_data)

        except FileNotFoundError as e:
            logging.error("File not found error: %s", e)
            raise
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON file: %s", e)
            raise
        except KeyError as e:
            logging.error("Missing expected key in JSON data: %s", e)
            raise
        except Exception as e:
            logging.error("Unexpected error extracting info data: %s", e)
            raise

    def save_to_csv(self, df: pd.DataFrame, output_file: str = DEFAULT_OUTPUT_FILE) -> None:
        """
        Saves the DataFrame to a CSV file.

        Args:
            df (pandas.DataFrame): The DataFrame to save.
            output_file (str, optional): The path to the output CSV file.
                Defaults to "instagram_profiles.csv".

        Raises:
            IOError: If there's an error writing to the file.
        """
        try:
            df.to_csv(output_file, index=False)
            logging.info("DataFrame saved to %s", output_file)
        except IOError as e:
            logging.error("Error saving DataFrame: %s", e)
            raise