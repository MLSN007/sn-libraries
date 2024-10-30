"""Facilitates the creation and management of Instagram posts.

This module provides classes and functions for creating, uploading, and managing
various types of Instagram posts, including photos, videos, reels, and albums
(carousels). It includes retry mechanisms for handling potential API errors.

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

from typing import List, Any, Optional, Dict, Union
from pathlib import Path
from instagrapi.exceptions import ClientError, MediaError
from instagrapi.types import Location, StoryHashtag, StoryLink, StoryMention, StorySticker, Media, Track, UserShort
from ig_client import IgClient
from ig_utils import IgUtils
from ig_data import IgPostData



# Get the logger
logger = logging.getLogger(__name__)

class IgPostManager:
    """Handles Instagram post operations using the IgClient.

    This class provides methods to upload and manage various types of Instagram posts.
    It includes a retry mechanism to handle temporary errors during uploads.

    Args:
        igcl (IgClient): The IgClient instance for Instagram interactions.
    """

    # Constants

    MAX_RETRIES = 3  # Increased from 1 to 3
    RETRY_DELAY = 10  # Increased from 5 to 10 seconds


    def __init__(self, igcl: IgClient) -> None:
        """
        Initializes the PostManager with an IgClient instance.

        Args:
            insta_client (IgClient): The IgClient instance to use for Instagram interactions.
        """
        self.client = igcl.client


    def _add_tags_and_mentions_to_caption(self, caption: str, hashtags: str, mentions: str) -> str:
        """
        Adds hashtags and mentions to a caption string.

        Args:
            caption (str): The original caption.
            hashtags (str): A string containing hashtags separated by spaces.
            mentions (str): A string containing mentions (usernames) separated by spaces.

        Returns:
            str: The modified caption with hashtags and mentions appended.
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
        Uploads a photo to Instagram.

        Args:
            (file_path): Path to the media file.
            caption (str, optional): Caption for the post (default: "").
            location (Location, optional): Location object for tagging (default: None).

        Returns:
            IgPostData: An IgPostData object representing the uploaded media.

        Raises:
            FileNotFoundError: If the media file is not found.
            ValueError: If the file format is not supported.
            MediaError: If there's an error during the upload process.
            ClientError: If there's a general Instagrapi client error.
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

    def upload_video(self, video_path: str, caption: str = "", location: Location = None) -> Optional[IgPostData]:
        """
        Uploads a video to Instagram.

        Args:
            video_path (str): Path to the video file
            caption (str, optional): Caption for the post (default: "")
            location (Location, optional): Location object for tagging (default: None)

        Returns:
            Optional[IgPostData]: An IgPostData object representing the uploaded media.

        Raises:
            FileNotFoundError: If the video file is not found
            ValueError: If the file format is not supported
            MediaError: If there's an error during the upload process
            ClientError: If there's a general Instagrapi client error
        """
        if not os.path.isfile(video_path):
            logger.error(f"Video file not found: {video_path}")
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # File extension validation
        valid_extensions = [".mp4"]
        if not video_path.lower().endswith(tuple(valid_extensions)):
            logger.error(f"Invalid file format: {video_path}. Only MP4 files are supported.")
            raise ValueError("Invalid file format. Only MP4 files are supported.")

        logger.info(f"Starting video upload process for: {video_path}")
        logger.info(f"File size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")

        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                extra_data = {}
                if location:
                    logger.info(f"Adding location data: {location.pk} - {location.name}")
                    extra_data["location"] = self.client.location_build(location)

                logger.info("Initiating video upload to Instagram...")
                # Add delay before upload attempt
                time.sleep(self.RETRY_DELAY)
                
                media = self.client.video_upload(
                    video_path, caption=caption, extra_data=extra_data
                )
                logger.info(f"Video upload successful. Media ID: {media.id}")

                # Create IgPostData object
                ig_video_post = IgPostData(
                    media_id=media.id,
                    media_type=media.media_type,
                    product_type=media.product_type,
                    caption=caption,
                    timestamp=media.taken_at,
                    media_url=media.thumbnail_url,
                    location_pk=location.pk if location else None,
                    location_name=location.name if location else None,
                    like_count=media.like_count,
                    comment_count=media.comment_count
                )

                return ig_video_post

            except (ClientError, MediaError) as e:
                logger.warning(
                    f"Error uploading video (attempt {retries + 1}/{self.MAX_RETRIES}): {e}. Retrying..."
                )
                retries += 1
                time.sleep(self.RETRY_DELAY * retries)  # Increasing delay between retries

        logger.error(f"Failed to upload video after {self.MAX_RETRIES} retries.")
        raise Exception(f"Failed to upload video after {self.MAX_RETRIES} retries")

    def upload_album(self, paths: List[str], caption: str = "", location: Location = None) -> List[IgPostData]:
        """Uploads an album to Instagram."""
        # File existence and extension validation
        valid_image_extensions = [".jpg", ".jpeg", ".png", ".webp"]  # Added more supported formats
        valid_video_extensions = [".mp4"]

        for path in paths:
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Media file not found: {path}")

            file_ext = os.path.splitext(path)[1].lower()
            if file_ext not in valid_image_extensions + valid_video_extensions:
                raise ValueError(
                    f"Invalid file format: {path}. Supported formats: {', '.join(valid_image_extensions + valid_video_extensions)}"
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

    def upload_reel(self, video_path: str, caption: str = "", location: Location = None) -> Optional[IgPostData]:
        """Uploads a reel to Instagram."""
        last_exception = None  # Track the last exception
        
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                extra_data = {}
                if location:
                    logger.info(f"Adding location data: {location.pk} - {location.name}")
                    extra_data["location"] = self.client.location_build(location)

                logger.info("Initiating reel upload to Instagram...")
                # Add delay before upload attempt
                time.sleep(self.RETRY_DELAY)
                
                media = self.client.clip_upload(
                    video_path, caption=caption, extra_data=extra_data
                )
                logger.info(f"Reel upload successful. Media ID: {media.id}")

                # Create IgPostData object
                ig_reel_post = IgPostData(
                    media_id=media.id,
                    media_type=media.media_type,
                    product_type=media.product_type,
                    caption=caption,
                    timestamp=media.taken_at,
                    media_url=media.thumbnail_url,
                    location_pk=location.pk if location else None,
                    location_name=location.name if location else None,
                    like_count=media.like_count,
                    comment_count=media.comment_count
                )

                return ig_reel_post

            except (ClientError, MediaError) as e:
                last_exception = e  # Store the exception
                logger.warning(
                    f"Error uploading reel (attempt {retries + 1}): {e}. Retrying..."
                )
                retries += 1
                time.sleep(self.RETRY_DELAY * retries)

        logger.error(f"Failed to upload reel after {self.MAX_RETRIES} retries.")
        if last_exception:
            raise last_exception
        else:
            raise Exception(f"Failed to upload reel after {self.MAX_RETRIES} retries")

    def upload_reel_with_music(self,
                                path: str,
                                caption: str,
                                track: Track,
                                location: Location = None     ##### this may be the cause of error
                                ) -> IgPostData:
        #### This Method is not working - but needs to be reviewed through the Instagrapi community
        """
        Uploads a reel to Instagram with a specified music track and an optional caption.
        (This method is not currently working and needs review.)

        Args:
            path (str): The path to the video file.
            caption (str, optional): The caption for the reel. Defaults to "".
            track (Track): The Track object representing the music to use.
            location (Location, optional): The location to tag in the post. Defaults to None.

        Returns:
            IgPostData: An IgPostData object representing the uploaded reel.

        Raises:
            FileNotFoundError: If the video file is not found.
            TypeError: If `track` is not a `Track` object.
            ValueError: If the video file format is not supported (only .mp4).
            ClientError: If there's an error from the Instagram API.
            MediaError: If there's an error uploading the media.
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

    def upload_story_photo(
        self,
        photo_path: str,
        caption: Optional[str] = None,
        mentions: Optional[List[Dict[str, Any]]] = None,
        hashtags: Optional[List[str]] = None,
        location: Optional[Location] = None,
        links: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Media]:
        """
        Upload a photo story to Instagram.

        Args:
            photo_path (str): Path to the photo file
            caption (Optional[str]): Story caption
            mentions (Optional[List[Dict[str, Any]]]): List of user mentions with positions
            hashtags (Optional[List[str]]): List of hashtags to include
            location (Optional[Location]): Location to tag in the story
            links (Optional[List[Dict[str, str]]]): List of links to add to the story

        Returns:
            Optional[Media]: The uploaded story media object if successful, None otherwise
        """
        try:
            # Prepare story mentions
            story_mentions = []
            if mentions:
                for mention in mentions:
                    user = UserShort(
                        pk=mention['user_id'],
                        username="",  # Will be filled by Instagram
                        full_name=""
                    )
                    story_mentions.append(
                        StoryMention(
                            user=user,
                            x=mention['x'],
                            y=mention['y'],
                            width=mention['width'],
                            height=mention['height']
                        )
                    )

            # Prepare story hashtags
            story_hashtags = []
            if hashtags:
                for idx, tag in enumerate(hashtags):
                    # Position hashtags vertically
                    y_position = 0.3 + (idx * 0.1)  # Adjust spacing as needed
                    story_hashtags.append(
                        StoryHashtag(
                            hashtag=tag,
                            x=0.5,  # Center horizontally
                            y=min(y_position, 0.8),  # Keep within bounds
                            width=0.4,
                            height=0.06
                        )
                    )

            # Prepare story links
            story_links = []
            if links:
                for idx, link in enumerate(links):
                    story_links.append(
                        StoryLink(
                            webUri=link['webUri'],
                            x=0.5,
                            y=0.9,  # Bottom of story
                            width=0.4,
                            height=0.06
                        )
                    )

            # Upload the story
            result = self.client.photo_upload_to_story(
                photo_path,
                caption=caption,
                mentions=story_mentions,
                hashtags=story_hashtags,
                links=story_links,
                location=location
            )

            logger.info(f"Successfully uploaded photo story")
            return result

        except Exception as e:
            logger.error(f"Error uploading photo story: {str(e)}")
            return None

    def upload_story_video(
        self,
        video_path: str,
        caption: Optional[str] = None,
        mentions: Optional[List[Dict[str, Any]]] = None,
        hashtags: Optional[List[str]] = None,
        location: Optional[Location] = None,
        links: Optional[List[Dict[str, str]]] = None
    ) -> Optional[Media]:
        """
        Upload a video story to Instagram.

        Args:
            video_path (str): Path to the video file
            caption (Optional[str]): Story caption
            mentions (Optional[List[Dict[str, Any]]]): List of user mentions with positions
            hashtags (Optional[List[str]]): List of hashtags to include
            location (Optional[Location]): Location to tag in the story
            links (Optional[List[Dict[str, str]]]): List of links to add to the story

        Returns:
            Optional[Media]: The uploaded story media object if successful, None otherwise
        """
        try:
            # Prepare story mentions
            story_mentions = []
            if mentions:
                for mention in mentions:
                    user = UserShort(
                        pk=mention['user_id'],
                        username="",  # Will be filled by Instagram
                        full_name=""
                    )
                    story_mentions.append(
                        StoryMention(
                            user=user,
                            x=mention['x'],
                            y=mention['y'],
                            width=mention['width'],
                            height=mention['height']
                        )
                    )

            # Prepare story hashtags
            story_hashtags = []
            if hashtags:
                for idx, tag in enumerate(hashtags):
                    # Position hashtags vertically
                    y_position = 0.3 + (idx * 0.1)  # Adjust spacing as needed
                    story_hashtags.append(
                        StoryHashtag(
                            hashtag=tag,
                            x=0.5,  # Center horizontally
                            y=min(y_position, 0.8),  # Keep within bounds
                            width=0.4,
                            height=0.06
                        )
                    )

            # Prepare story links
            story_links = []
            if links:
                for idx, link in enumerate(links):
                    story_links.append(
                        StoryLink(
                            webUri=link['webUri'],
                            x=0.5,
                            y=0.9,  # Bottom of story
                            width=0.4,
                            height=0.06
                        )
                    )

            # Upload the story
            result = self.client.video_upload_to_story(
                video_path,
                caption=caption,
                mentions=story_mentions,
                hashtags=story_hashtags,
                links=story_links,
                location=location
            )

            logger.info(f"Successfully uploaded video story")
            return result

        except Exception as e:
            logger.error(f"Error uploading video story: {str(e)}")
            return None





