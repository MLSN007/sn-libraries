"""
ig_post_manager.py:
Facilitates the creation and management of various types of
Instagram posts (photos, videos, albums/carousels)
including the ability to add music to videos.
"""
import os  # Import the os module for file system operations
import logging  # For logging errors
from instagrapi.types import Location, StoryHashtag, StoryLink, StoryMention, StorySticker 
from ig_client import IgClient # Note the updated import path
from ig_data import IgPost  # Import the IgPost class

class IgPostManager:  
    def __init__(self, insta_client: IgClient):
        """
        Initializes the PostManager with an IgClient instance.

        Args:
            insta_client: The IgClient instance to use for Instagram interactions.
        """
        self.client = insta_client.client


    def upload_photo(self, photo_path, caption="", location_pk=None):
        """
        Uploads a single photo to Instagram.

        Args:
            photo_path (str): The path to the photo file.
            caption (str, optional): The caption for the photo. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.

        Returns:
            IgPost: An object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the photo file is not found.
            Exception: If there is an error during the upload process.
        """

        try:
            # Check if the file exists
            if not os.path.exists(photo_path):
                raise FileNotFoundError(f"Photo not found at: {photo_path}")

            # If location_pk is provided, create a Location object
            location = None
            if location_pk:
                location = Location(
                    pk=location_pk, 
                    name="Malecón Cisneros - Miraflores"  # Use the actual name here
                )
            
            # Upload the photo with the Location object
            media = self.client.photo_upload(
                photo_path, 
                caption=caption, 
                location=location 
            )
            
            # Create IgPost object to store post information
            ig_post = IgPost(
                media_id=media.pk,
                media_type="photo",
                caption=caption,
                timestamp=media.taken_at,
                location=media.location,
                like_count=media.like_count,
                comment_count=media.comment_count
            )
            
            return ig_post
            
        except FileNotFoundError as e:
            logging.error(f"File not found error: {e}")
            raise  # Re-raise the exception after logging
        except Exception as e:
            logging.error(f"Error uploading photo: {e}")
            raise  # Re-raise the exception after logging



    def upload_video(self, video_path, caption=""):
        try:
            return self.client.video_upload(video_path, caption=caption)
        except Exception as e:
            raise Exception(f"Error uploading video: {e}")

    def upload_album(self, paths, caption=""):
        try:
            media = []
            for path in paths:
                if path.endswith((".jpg", ".jpeg", ".png")):
                    media.append(self.client.photo_upload(path))
                elif path.endswith((".mp4", ".mov")):
                    media.append(self.client.video_upload(path))
            return self.client.album_upload(media, caption=caption)
        except Exception as e:
            raise Exception(f"Error uploading album: {e}") from e


    def upload_video_with_music(self, video_path, music_path, caption=""):
        """
        Uploads a video to Instagram with a specified music track and an optional caption.

        Args:
            video_path: The path to the video file.
            music_path: The path to the music file (supported formats: .mp3, .m4a).
            caption: (Optional) The caption for the video.

        Returns:
            The Instagrapi Media object representing the uploaded video with music.
        """

        try:
            return self.client.video_upload(video_path, caption=caption, audio_path=music_path)
        except Exception as e:
            raise Exception(f"Error uploading video with music: {e}")

    def search_music(self, query):
        """
        Searches for music tracks on Instagram based on a query.

        Args:
            query: The search query for music.

        Returns:
            A list of MusicTrack objects matching the query.
        """
        try:
            return self.client.music_search(query)
        except Exception as e:
            raise Exception(f"Error searching for music: {e}")

    def upload_reel_with_music(self, video_path, music_track_id, caption=""):
        """
        Uploads a Reel to Instagram with a specified music track ID and an optional caption.
        (Note: Reel-specific features like effects are not yet implemented.)

        Args:
            video_path: The path to the video file.
            music_track_id: The ID of the music track to use (obtained from `search_music`).
            caption: (Optional) The caption for the Reel.

        Returns:
            The Instagrapi Media object representing the uploaded Reel.
        """
        try:
            return self.client.clip_upload(video_path, caption=caption, music_id=music_track_id)
        except Exception as e:
            raise Exception(f"Error uploading Reel with music: {e}")
