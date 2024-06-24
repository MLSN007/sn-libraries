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
                location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores")

            # Upload the photo
            media = self.client.photo_upload(
                photo_path, caption=caption, location=location
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
            raise
        except Exception as e:
            logging.error(f"Error uploading photo: {e}")
            raise



    def upload_video(self, video_path, caption="", location_pk=None):
        """
        Uploads a single video to Instagram.

        Args:
            video_path (str): The path to the video file.
            caption (str, optional): The caption for the video. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.

        Returns:
            IgPost: An object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the video file is not found.
            Exception: If there is an error during the upload process.
        """

        try:
            # Check if the file exists
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video not found at: {video_path}")

            # If location_pk is provided, create a Location object
            location = None
            if location_pk:
                location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores")

            # Upload the video
            media = self.client.video_upload(video_path, caption=caption, location=location)
            
            # Create IgPost object to store post information
            ig_post = IgPost(
                media_id=media.pk,
                media_type="video",  # Updated media_type for videos
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
        except Exception as e:
            logging.error(f"Error uploading video: {e}")
            raise

    def upload_album(self, paths, caption, location_pk=None):
        """
        Uploads a carousel/album post to Instagram with an optional caption and location.

        Args:
            paths (list): A list of paths to photo and/or video files.
            caption (str, optional): The caption for the album. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.

        Returns:
            IgPost: An object containing information about the uploaded album.

        Raises:
            FileNotFoundError: If any of the media files are not found.
            Exception: If there is an error during the upload process.
        """

        try:
            media = []
            for path in paths:  # Correctly indented for loop
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Media file not found at: {path}")

            if path.endswith((".jpg", ".jpeg", ".png")):
                media.append(self.client.photo_upload(path, caption=caption))
            elif path.endswith((".mp4", ".mov")):
                media.append(self.client.video_upload(path, caption=caption))


            # If location_pk is provided, create a Location object
            location = None
            if location_pk:
                location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores")

            # Upload the album
            album = self.client.album_upload(media, caption=caption, location=location)
            album = self.client.album_upload(media, caption=caption, location=location)
            # Create IgPost object to store post information
            ig_post = IgPost(
                media_id=album.pk,
                media_type="album",  # Updated media_type for albums
                caption=caption,
                timestamp=album.taken_at,
                location=album.location,
                like_count=album.like_count,
                comment_count=album.comment_count
            )

            return ig_post

        except FileNotFoundError as e:
            logging.error(f"File not found error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error uploading album: {e}")
            raise


def search_music(self, query):
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
    """
    Uploads a video to Instagram with a specified music track, caption, and optional location.

    Args:
        video_path (str): The path to the video file.
        music_path (str): The path to the music file (supported formats: .mp3, .m4a).
        caption (str, optional): The caption for the video. Defaults to "".
        location_pk (int, optional): The location PK to tag in the post. Defaults to None.

    Returns:
        IgPost: An object containing information about the uploaded video.

    Raises:
        FileNotFoundError: If either the video or music file is not found.
        Exception: If there is an error during the upload process.
    """

    try:
        # Check if files exist
        for file_path in [video_path, music_path]:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found at: {file_path}")

        # Create Location object if provided
        location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores") if location_pk else None

        # Upload video with music
        media = self.client.video_upload(video_path, caption=caption, audio_path=music_path, location=location)

        return IgPost(
            media_id=media.pk,
            media_type="video",
            caption=caption,
            timestamp=media.taken_at,
            location=media.location,
            like_count=media.like_count,
            comment_count=media.comment_count
        )
    except FileNotFoundError as e:
        logging.error(f"File not found error: {e}")
        raise
    except Exception as e:
        logging.error(f"Error uploading video with music: {e}")
        raise


def upload_reel_with_music(self, video_path, music_track_id, caption="", location_pk=None):
    """
    Uploads a Reel to Instagram with a specified music track, caption, and optional location.

    Args:
        video_path (str): The path to the video file.
        music_track_id (str): The ID of the music track to use.
        caption (str, optional): The caption for the Reel. Defaults to "".
        location_pk (int, optional): The location PK to tag in the post. Defaults to None.

    Returns:
        IgPost: An object containing information about the uploaded Reel.

    Raises:
        FileNotFoundError: If the video file is not found.
        Exception: If there is an error during the upload process.
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found at: {video_path}")

        location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores") if location_pk else None
        media = self.client.clip_upload(video_path, caption=caption, music_id=music_track_id, location=location)

        return IgPost(
            media_id=media.pk,
            media_type="reel",
            caption=caption,
            timestamp=media.taken_at,
            location=media.location,
            like_count=media.like_count,  
            comment_count=media.comment_count
        )
    except FileNotFoundError as e:
        logging.error(f"File not found error: {e}")
        raise
    except Exception as e:
        logging.error(f"Error uploading reel with music: {e}")
        raise
