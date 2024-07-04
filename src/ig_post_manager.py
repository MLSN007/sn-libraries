"""
ig_post_manager.py:
Facilitates the creation and management of various types of Instagram posts (photos, videos, albums/carousels).

Media types:
Photo - When media_type=1
Video - When media_type=2 and product_type=feed
IGTV - When media_type=2 and product_type=igtv
Reel - When media_type=2 and product_type=clips
Album - When media_type=8

"""
import os
import time
import datetime
import logging

from typing import List, Any, Optional
from instagrapi.exceptions import ClientError, MediaError
from instagrapi.types import Location, StoryHashtag, StoryLink, StoryMention, StorySticker, Media, Track
from ig_client import IgClient
from ig_utils import IgUtils
from ig_data import IgPostData



# Get the logger
logger = logging.getLogger(__name__)

class IgPostManager:
    """Handles Instagram post operations using the IgClient."""
    
    MAX_RETRIES = 1  # Maximum number of retries
    RETRY_DELAY = 5  # Delay between retries in seconds


    def __init__(self, igcl: IgClient) -> None:
        """
        Initializes the PostManager with an IgClient instance.

        Args:
            insta_client (IgClient): The IgClient instance to use for Instagram interactions.
        """
        self.client = igcl.client


    def _add_tags_and_mentions_to_caption(self, caption: str, hashtags: str, mentions: str) -> str:
        """
        Adds hashtags and mentions to the caption.

        Args:
            caption (str): The original caption.
            hashtags (List[str]): List of hashtags to add.
            mentions (List[str]): List of usernames to mention.

        Returns:
            str: The caption with added hashtags and mentions.
        """


        print("Hashtags type:", type(hashtags))
        print("Hashtags value:", hashtags)
        print("Mentions type:", type(mentions))
        print("Mentions value:", mentions)
    
        caption_with_tags = caption + " " + hashtags
        caption_with_mentions = caption_with_tags + " " + mentions
        return caption_with_mentions

    def upload_photo(self, photo_path: str, caption: str = "", location: Location = None
                     ) -> IgPostData:
        """
        Uploads a single photo to Instagram and returns an IgPostData object.

        Args:
            photo_path (str): The path to the photo file.
            caption (str, optional): The caption for the photo. Defaults to "".
                                        caption already includes tags and mentions.
            location (Location object, optional): The location object to tag in the post. Defaults to None.

        Returns:
            Media: An instagrapi object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the photo file is not found.
            ClientError: If there's an error from the Instagram API.
        """

        valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        if not photo_path.lower().endswith(tuple(valid_extensions)):
            raise ValueError(
                "Invalid file format. Only JPG/JPEG/PNG/WEBP files are supported."
            )
        
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                media = self.client.photo_upload(
                    photo_path, caption=caption, location=location
                )

                # Create IgPostData object directly from the returned Media object
                ig_photo_post = IgPostData(
                    media_id=media.id,
                    media_type=media.media_type,
                    product_type=media.product_type,
                    caption=caption,  
                    timestamp=media.taken_at,
                    media_url=media.thumbnail_url,  
                    location_pk=location.pk if location else None,  # Extract location ID
                    location_name=location.name if location else None, # Extract location name
                    like_count=media.like_count,
                    comment_count=media.comment_count,
                )
                return ig_photo_post

            except (ClientError, MediaError) as e:
                logger.warning(
                    f"Error uploading photo (attempt {retries + 1}): {e}. Retrying..."
                )
                retries += 1
                delay = self.RETRY_DELAY * retries  # Increasing delay with each retry
                time.sleep(delay)  # Increasing delay with each retry

        logger.error(f"Failed to upload photo after {self.MAX_RETRIES} retries.")
        raise e  # Raise the final exception after retries are exhausted

    def upload_video(
        self, video_path: str, caption: str = "", location: Location = None
        ) -> IgPostData:
        """
        Uploads a video to Instagram with retry logic.
        """

        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # File extension validation
        valid_extensions = [".mp4"]  # Add more video extensions if needed
        if not video_path.lower().endswith(tuple(valid_extensions)):
            raise ValueError(
                "Invalid file format. Only MP4 files are supported."
            )

        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                extra_data = {}
                if location:
                    extra_data["location"] = self.client.location_build(location)
                
                media = self.client.video_upload(
                    video_path, caption=caption, extra_data=extra_data
                )

                # Create IgPostData object directly from the returned Media object
                ig_video_post = IgPostData(
                    media_id=media.id,
                    media_type=media.media_type,
                    product_type=media.product_type,
                    caption=caption,  
                    timestamp=media.taken_at,
                    media_url=media.thumbnail_url,  
                    location_pk=location.pk if location else None,  # Extract location ID
                    location_name=location.name if location else None,  # Extract location name
                    like_count=media.like_count,
                    comment_count=media.comment_count
                )

                return ig_video_post

            except (ClientError, MediaError) as e:
                logger.warning(
                    f"Error uploading video (attempt {retries + 1}): {e}. Retrying..."
                )
                retries += 1
                time.sleep(self.RETRY_DELAY * retries)

        logger.error(f"Failed to upload video after {self.MAX_RETRIES} retries.")
        raise e  # Raise the final exception after retries are exhausted

    def upload_album(self,
                     paths: List[str], caption: str = "", location: Location = None
                     ) -> List[IgPostData]:
        """
        Uploads a carousel/album post to Instagram with retry logic and file validation.
        """

        # File existence and extension validation
        valid_image_extensions = [".jpg"]
        valid_video_extensions = [".mp4"]

        for path in paths:
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Media file not found: {path}")

            file_ext = os.path.splitext(path)[1].lower()
            if file_ext not in valid_image_extensions + valid_video_extensions:
                raise ValueError(
                    f"Invalid file format: {path}. Only JPG/JPEG/PNG/WEBP/MP4 files are supported in albums."
                )

        retries = 0
        while retries < self.MAX_RETRIES:
            try:

                media = self.client.album_upload(paths, caption=caption, location=location)

                # Create a single IgPostData object for the entire album
                ig_post_data = IgPostData(
                    media_id=media.id,
                    media_type=media.media_type,
                    product_type=media.product_type,
                    caption=caption,  
                    timestamp=media.taken_at,  
                    media_url=media.thumbnail_url,  # You might need to adjust this for albums
                    location_pk=location.pk if location else None,  
                    location_name=location.name if location else None,  
                    like_count=0,
                    comment_count=0,
                    is_album=True,
                    album_media_ids=[m.pk for m in media.resources],
                    album_media_urls=[m.thumbnail_url for m in media.resources]  # Extract URLs
                )

                return ig_post_data  # Return the single IgPostData object
            except (ClientError, MediaError) as e:
                logger.warning(
                    f"Error uploading album (attempt {retries + 1}): {e}. Retrying..."
                )
                retries += 1
                time.sleep(self.RETRY_DELAY * retries)

        logger.error(f"Failed to upload album after {self.MAX_RETRIES} retries.")
        raise e

    def upload_reel(self,
                    video_path: str, caption: str = "", location: Location = None
                    ) -> IgPostData:
        """
        Uploads a Reel as it is to Instagram.

        Args:
            video_path (str): The path to the video file.
            caption (str, optional): The caption for the video/Reel. Defaults to "".
                                        caption already includes tags and mentions.
            location (Location object, optional): The location object to tag in the post. Defaults to None.

        Returns:
            Media: An instagrapi object containing information about the uploaded video/Reel.

        Raises:
            FileNotFoundError: If the video file is not found.
            ClientError: If there's an error from the Instagram API.
        """
        
        # Check if file exists
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # File extension validation
        valid_extensions = [".mp4"]  
        if not video_path.lower().endswith(tuple(valid_extensions)):
            raise ValueError(
                "Invalid file format. Only MP4 files are supported for reels."
            )

        retries = 0
        while retries < self.MAX_RETRIES:
            try:
        
                media = self.client.clip_upload(video_path, caption=caption, location=location)
                print("reel outcome: ---------------------------------------------------------------------------------")
                print(media)

                # Create IgPostData object from the uploaded reel
                ig_reel_post = IgPostData(
                    media_id=media.id,
                    media_type=media.media_type,
                    caption=caption,
                    timestamp=media.taken_at,
                    media_url=media.thumbnail_url,
                    location_pk=location.pk if location else None,
                    location_name=location.name if location else None,
                    like_count=media.like_count,
                    comment_count=media.comment_count,
                )

                return ig_reel_post

            except (ClientError, MediaError) as e:
                logger.warning(
                    f"Error uploading reel (attempt {retries + 1}): {e}. Retrying..."
                )
                retries += 1
                time.sleep(self.RETRY_DELAY * retries)

        logger.error(f"Failed to upload reel after {self.MAX_RETRIES} retries.")
        raise e  # Raise the final exception after retries are exhausted




    def upload_reel_with_music(self,
                                path: str,
                                caption: str,
                                track: Track,
                                location: Location = None     ##### this may be the cause of error
                                ) -> IgPostData:
        #### This Method is not working - but needs to be reviewed through the Instagrapi community
        """
        Uploads a reel to Instagram with a specified music track and an optional caption.
           using instagrapi method:
           clip_upload_as_reel_with_music(path: Path, caption: str, track: Track, extra_data: Dict = {})

        Args:
            video_path (str): The path to the video file.
            music_path (str): The path to the music file (supported formats: .mp3, .m4a).
            caption (str, optional): The caption for the video. Defaults to "".
            location (Location, optional): The location to tag in the post. Defaults to None.

        Returns:
            Media: An instagrapi object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the video or music file is not found.
            ClientError: If there's an error with the Instagram client.
            Exception: If there is an error during the upload process.
        """

        # Check if file exists
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Video file not found: {path}")

        # File extension validation
        valid_extensions = [".mp4"]  # Add more video extensions if needed
        if not path.lower().endswith(tuple(valid_extensions)):
            raise ValueError(
                "Invalid file format. Only MP4 files are supported for reels."
            )

        # Ensure track is of type Track
        if not isinstance(track, Track):
            raise TypeError(f"Invalid track type. Expected Track object, got {type(track)}")

        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                media = self.client.clip_upload_as_reel_with_music(
                    path, caption=caption, track=track, location=location
                )

                ig_reel_post = IgPostData(
                    media_id=media.id,
                    media_type=media.media_type,
                    product_type=media.product_type,
                    caption=caption,  
                    timestamp=media.taken_at,
                    media_url=media.thumbnail_url,  
                    location_pk=location.pk if location else None,  # Extract location ID
                    location_name=location.name if location else None,  # Extract location name
                    like_count=media.like_count,
                    comment_count=media.comment_count
                )

        
                return ig_reel_post  # Return the IgPostData object
            except (ClientError, MediaError) as e:
                logger.warning(
                    f"Error uploading reel with music (attempt {retries + 1}): {e}. Retrying..."
                )
                retries += 1
                time.sleep(self.RETRY_DELAY * retries)

        logger.error(
            f"Failed to upload reel with music after {self.MAX_RETRIES} retries."
        )
        raise e  # Raise the final exception after retries are exhausted

