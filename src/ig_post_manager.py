"""
ig_info_fetcher.py: Fetches Instagram user information using the HikerAPI.
"""

import os
import json
import logging
from typing import Dict, List, Optional
from hikerapi import Client
from hikerapi.exceptions import HikerAPIException

DEFAULT_OUTPUT_FILE = "instagram_info.json"

class IgInfoFetcher:
    """A class for fetching Instagram user information using the HikerAPI."""

    def __init__(self, api_key: Optional[str] = os.environ.get("HikerAPI_key")) -> None:
        """
        Initializes the IgInfoFetcher with the HikerAPI key.

        Args:
            api_key (str, optional): Your HikerAPI key. Defaults to the value of the environment variable HikerAPI_key.

        Raises:
            ValueError: If the HikerAPI_key environment variable is not set.
        """
        if not api_key:
            raise ValueError("HikerAPI_key environment variable not found.")
        self.client = Client(token=api_key)

    def fetch_info(self, username: str) -> Optional[Dict]:
        """
        Fetches information for a single Instagram user.

        Args:
            username (str): The Instagram username.

        Returns:
            Optional[Dict]: A dictionary containing the user's information if successful, otherwise None.
        """
        try:
            user_info = self.client.user_by_username_v2(username)
            if user_info["status"] == "ok":
                return user_info
            else:
                logging.error("Error fetching data for %s: %s", username, user_info.get("error"))
        except HikerAPIException as e:
            logging.error("HikerAPI error for %s: %s", username, e)
        except Exception as e:
            logging.error("Unexpected error fetching data for %s: %s", username, e)
        return None

    def fetch_and_save_info(self, usernames: List[str], output_file: str = DEFAULT_OUTPUT_FILE) -> None:
        """
        Fetches information for multiple Instagram users and saves it to a JSON file.

        Args:
            usernames (List[str]): A list of Instagram usernames.
            output_file (str, optional): The path to the output JSON file. Defaults to "instagram_info.json".
        """
        all_info_data = []
        for username in usernames:
            info_data = self.fetch_info(username)
            if info_data:
                all_info_data.append(info_data)
            else:
                logging.warning("Failed to fetch info for %s", username)

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_info_data, f, ensure_ascii=False, indent=4)
            logging.info("Saved %d profiles to %s", len(all_info_data), output_file)
        except IOError as e:
            logging.error("Error saving data to file %s: %s", output_file, e)

# ---------------------------------------------------------------------------
# -----------  these methods need further review  ---------------------------
# ---------------------------------------------------------------------------

    def search_music(self, query):
        #### This Method is not working - but needs to be reviewed through the Instagrapi community
        """
        Searches for music tracks on Instagram based on a query.

        Args:
            query (str): The search query for music.

        Returns:
            list: A list of MusicTrack objects matching the query.

        Raises:
            Exception: If there is an error searching for music.
        """
        try:
            return self.client.music_search(query)
        except Exception as e:
            logging.error(f"Error searching for music: {e}")
            raise Exception(f"Error searching for music: {e}")



    def upload_video_with_music(self, video_path, music_path, caption="", location_pk=None):
        #### This Method is not working - but needs to be reviewed through the Instagrapi community
        """
        Uploads a video to Instagram with a specified music track and an optional caption.

        Args:
            video_path (str): The path to the video file.
            music_path (str): The path to the music file (supported formats: .mp3, .m4a).
            caption (str, optional): The caption for the video. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.

        Returns:
            IgPost: An object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the video or music file is not found.
            ClientError: If there's an error with the Instagram client.
            Exception: If there is an error during the upload process.
        """

        try:
            # Check if files exist
            for path in [video_path, music_path]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"File not found at: {path}")

            # Load music from path
            audio = self.client.upload_album(
                [video_path, music_path], 
                caption=caption, 
                media_type='reel'
            )
            ###################################
            ###### REWRITE FOLLOWING THE LOGIC OF THE FIRST THREE UPLOAD METHODS
            ####################################
            # If location_pk is provided, create a Location object
            location = None
            if location_pk:
                location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores")

            # Upload the video with music ID
            media = self.client.video_upload(
                video_path, 
                caption=caption, 
                audio_id=audio.id,  # Pass the music track ID
                location=location
            )

            # Create IgPost object to store post information
            ig_post = IgPost(
                media_id=media.pk,
                media_type="video",
                caption=caption,
                timestamp=media.taken_at,
                location=media.location,
                like_count=media.like_count,
                comment_count=media.comment_count
            )
            
            return ig_post
        
        except FileNotFoundError as e:
            logging.error(f"File not found error: {e}")
            raise
        except ClientError as e:
            logging.error(f"Instagram API error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error uploading video with music: {e}")
            raise


    def upload_reel_with_music(self, video_path, music_path, caption="", location_pk=None):
        """
        Uploads a Reel to Instagram with a specified music track, caption, and optional location.

        Args:
            video_path (str): The path to the video file.
            music_path (str): The path to the music file (supported formats: .mp3, .m4a).
            caption (str, optional): The caption for the Reel. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.

        Returns:
            IgPost: An object containing information about the uploaded Reel.

        Raises:
            FileNotFoundError: If the video or music file is not found.
            ClientError: If there's an error with the Instagram client.
            Exception: If there is an error during the upload process.
        """
        try:
            # Check if files exist
            for path in [video_path, music_path]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"File not found at: {path}")

            # Validate file types
            valid_video_extensions = ('.mp4', '.mov')
            valid_audio_extensions = ('.mp3', '.m4a')
            if not video_path.endswith(valid_video_extensions):
                raise ClientError(f"Unsupported video format: {video_path}")
            if not music_path.endswith(valid_audio_extensions):
                raise ClientError(f"Unsupported audio format: {music_path}")
            
            ###################################
            ###### REWRITE FOLLOWING THE LOGIC OF THE FIRST THREE UPLOAD METHODS
            ####################################
            
            # If location_pk is provided, create a Location object
            location = None
            if location_pk:
                location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores")

            # Combine audio and video
            videoclip = VideoFileClip(video_path)
            audioclip = AudioFileClip(music_path)
            final_clip = CompositeVideoClip([videoclip], audio=audioclip)

            # Write the combined clip to a temporary file
            combined_path = video_path.replace(".mp4", "_with_music.mp4")
            final_clip.write_videofile(combined_path, codec='libx264', audio_codec='aac')

            # Upload the reel with the music
            media = self.client.clip_upload(combined_path, caption=caption, location=location)
            os.remove(combined_path) #Remove temporary file

            # Create IgPost object to store post information
            ig_post = IgPost(
                media_id=media.pk,
                media_type="reel",
                caption=caption,
                timestamp=media.taken_at,
                location=media.location,
                like_count=media.like_count,
                comment_count=media.comment_count
            )
            
            return ig_post
        
        except FileNotFoundError as e:
            logging.error(f"File not found error: {e}")
            raise
        except ClientError as e:
            logging.error(f"Unsupported media format or client error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error uploading reel with music: {e}")
            raise