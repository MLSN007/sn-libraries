"""
ig_post_manager.py:
Facilitates the creation and management of various types of
Instagram posts (photos, videos, albums/carousels)
including the ability to add music to videos.
"""
import os  # Import the os module for file system operations
import logging  # For logging errors
import time

from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from instagrapi.exceptions import ClientError, AlbumConfigureError
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



    def upload_reel(self, video_path, caption="", location_pk=None):
        """
        Uploads a single reel to Instagram.

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

    def upload_album(self, paths, caption="", location_pk=None, max_retries=3, retry_delay=5):
        """
        Uploads a carousel/album post to Instagram with optional caption, location,
        and retry mechanisms for handling errors.

        Args:
            paths (list): A list of paths to photo and/or video files.
            caption (str, optional): The caption for the album. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.
            max_retries (int, optional): Maximum number of retries in case of errors. Defaults to 3.
            retry_delay (int, optional): Delay in seconds between retries. Defaults to 5.

        Returns:
            IgPost: An object containing information about the uploaded album.

        Raises:
            FileNotFoundError: If any of the media files are not found.
            Exception: If the maximum retries are exceeded and the upload still fails.
        """

        retries = 0
        while retries < max_retries:
            try:
                media = []
                for path in paths:
                    if not os.path.exists(path):
                        raise FileNotFoundError(f"Media file not found at: {path}")

                    if path.endswith((".jpg", ".jpeg", ".png")):
                        media.append(self.client.photo_upload(path, caption))
                    elif path.endswith((".mp4", ".mov")):
                        media.append(self.client.video_upload(path, caption))

                # If location_pk is provided, create a Location object
                location = None
                if location_pk:
                    location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores")

                # Upload the album
                album = self.client.album_upload(media, caption=caption, location=location)

                # Create IgPost object to store post information
                ig_post = IgPost(
                    media_id=album.pk,
                    media_type="album",
                    caption=caption,
                    timestamp=album.taken_at,
                    location=album.location,
                    like_count=album.like_count,
                    comment_count=album.comment_count
                )

                return ig_post

            except (FileNotFoundError, ClientError, AlbumConfigureError) as e:
                logging.error(f"Error during album upload (attempt {retries + 1}/{max_retries}): {e}")
                if retries < max_retries - 1:  # Only retry if attempts remain
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retries += 1
                else:
                    raise  # Re-raise the exception if max retries reached


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