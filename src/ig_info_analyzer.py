"""
ig_info_analyzer.py: Extracts and analyzes Instagram user information from a JSON file.
"""
import json
import logging
import pandas as pd


class IgInfoAnalyzer:
    """A class for extracting and analyzing Instagram user information."""

    def extract_info_data_from_json(self, input_file="instagram_info.json"):
        """
        Loads Instagram user information from a JSON file
        and extracts relevant fields into a Pandas DataFrame.

        Args:
            input_file (str, optional): The path to the input JSON file.
            Defaults to "instagram_info.json".

        Returns:
            pandas.DataFrame: A DataFrame containing the extracted user information.
        """

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                all_info_data = json.load(f)

            extracted_data = []
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
        except Exception as e:
            logging.error("Error extracting info data: %s", e)
            raise

    def save_to_csv(self, df, output_file="instagram_profiles.csv"):
        """Saves the DataFrame to a CSV file."""
        try:
            df.to_csv(output_file, index=False)
            logging.info("DataFrame saved to %s", output_file)
        except Exception as e:
            logging.error("Error saving DataFrame: %s", e)
            raise

