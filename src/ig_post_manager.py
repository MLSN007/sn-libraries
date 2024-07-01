"""
ig_post_manager.py:
Facilitates the creation and management of various types of Instagram posts (photos, videos, albums/carousels).
"""
import os
import time
import datetime
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from instagrapi import Client
from instagrapi.exceptions import ClientError, MediaError
from instagrapi.types import Location, StoryHashtag, StoryLink, StoryMention, StorySticker, Media, Track
from ig_client import IgClient
from ig_utils import IgPost, IgUtils

MAX_RETRIES = 3
RETRY_DELAY = 5

class IgPostManager:
    """Handles Instagram post operations using the IgClient."""

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

    def upload_photo(self, photo_path: str, caption: str = "", location: Location = None) -> IgPost:
        """
        Uploads a single photo to Instagram and returns an IgPost object.

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
        
        print("Photo path:", photo_path)
        print("Caption:", caption)
        print("Location Type:",type(location))
        print("Location:", location)


        # post = self.client.photo_upload(photo_path, caption, location)
        
        media= self.client.photo_upload(
            photo_path,
            caption=caption,
            location=location
        )
          # Create IgPost object directly from the returned Media object
        post = IgPost(
            media_id=media.id,
            media_type=media.media_type,
            caption=caption,  # Pass the caption directly
            timestamp=media.taken_at,
            media_url=media.thumbnail_url, 
            location=location,
            like_count=0,  # Set initial like count (it might be 0 when just uploaded)
            comment_count=0,  
            usertags=media.usertags,
        )

        return post


    def upload_video(self, video_path: str, caption: str = "", location: Location = None) -> Media:
        """
        Uploads a video (or Reel without music) to Instagram.

        Args:
            video_path (str): The path to the video file.
            caption (str, optional): The caption for the video/Reel. Defaults to "".
                                        caption already includes tags and mentions.
            location (Location object, optional): The location object to tag in the post. Defaults to None.

        Returns:
            Media: An instagrapi object containing information about the uploaded video.

        Raises:
            FileNotFoundError: If the video file is not found.
            ClientError: If there's an error from the Instagram API.
        """
        video = self.client.video_upload(video_path, caption, location)
        
        return video



    def upload_reel(self, video_path: str, caption: str = "", location: Location = None) -> Media:
        """
        Uploads a Reel without additional music to Instagram.

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
        
        reel = self.client.reel_upload(video_path, caption, location)

        return reel


    def upload_album(self, paths: List[str], caption: str = "", location: Location = None) -> Media:
        """
        Uploads a carousel/album post to Instagram.

        Args:
            paths (List[str]): A list of paths to photo and/or video files.
            caption (str, optional): The caption for the album. Defaults to "".
                                        caption already includes tags and mentions.
            location (Location object, optional): The location object to tag in the post. Defaults to None.

        Returns:
           Media: An instagrapi object containing information about the uploaded album.

        Raises:
            FileNotFoundError: If any of the media files are not found.
            ClientError: If there's an error from the Instagram API.
        """
        
        album = self.client.album_upload(paths, caption, location)

        return album


    def upload_reel_with_music(self,
                                path: str,
                                caption: str,
                                track: Track,
                                location: Location = None     ##### this may be the cause of error
                                ) -> Media:
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

        # Pending to add checks such as if the file exists and if track is of Track type

        
        reel = self.client.clip_upload_as_reel_with_music(
            path=path, caption=caption, track=track, location=location)
        
        return reel

