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
from instagrapi.types import Location, StoryHashtag, StoryLink, StoryMention, StorySticker
from ig_client import IgClient
from ig_data import IgPost

MAX_RETRIES = 3
RETRY_DELAY = 5

class IgPostManager:
    """Handles Instagram post operations using the IgClient."""

    def __init__(self, insta_client: IgClient) -> None:
        """
        Initializes the PostManager with an IgClient instance.

        Args:
            insta_client (IgClient): The IgClient instance to use for Instagram interactions.
        """
        self.client = insta_client.client

    def _upload_media(self, upload_func: Any, media_type: str, *args: Any, max_retries: int = MAX_RETRIES, retry_delay: int = RETRY_DELAY, **kwargs: Any) -> IgPost:
        """
        Generic helper function to upload media (photo, video, album) with retries.

        Args:
            upload_func (Any): The function to use for uploading.
            media_type (str): The type of media being uploaded ("photo", "video", "album").
            *args: Variable length argument list for the upload function.
            max_retries (int): Maximum number of retry attempts.
            retry_delay (int): Delay between retries in seconds.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            IgPost: An object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the media file is not found.
            ClientError: If there's an error from the Instagram API.
            MediaError: If there's an error processing the media.
        """
        caption = kwargs.get('caption', '')
        caption_with_tags_and_mentions = self._add_tags_and_mentions_to_caption(
            caption, kwargs.get('hashtags', ''), kwargs.get('mentions', '')
        )

        location_pk = kwargs.get("location_pk")
    
        # Fetch location details including name
        location = None
        if location_pk is not None and not pd.isna(location_pk):  # Check if location_pk is valid
            try:
                location_info = self.client.location_complete(location_pk)  # Use location_complete
                location = Location(
                    pk=location_pk,
                    name=location_info.name,  
                    address=location_info.address,
                    lat=location_info.lat,
                    lng=location_info.lng,
                )
            except ClientError as e:
                logging.error(f"Error fetching location details: {e}")

        print("location_pk:", location_pk)
        print("Location type:", type(location))
        print("Location value:", location)


        retries = 0
        while retries < max_retries:
            try:
                # Pass location as a keyword argument
                media = upload_func(*args, caption_with_tags_and_mentions, location=location)  
                return IgPost(
                    media_id=media.pk,
                    media_type=media_type,
                    caption=caption_with_tags_and_mentions,
                    timestamp=media.taken_at,
                    location=media.location,
                    like_count=media.like_count,
                    comment_count=media.comment_count,
                    published=True,
                    tags=kwargs.get('hashtags', []),
                    mentions=kwargs.get('mentions', [])
                )
            except (FileNotFoundError, ClientError, MediaError) as e:
                logging.error(f"Error during {media_type} upload (attempt {retries + 1}/{max_retries}): {e}")
                retries += 1
                if retries < max_retries:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    return IgPost(
                        published=False,
                        failed_attempts=retries,
                        last_failed_attempt=datetime.datetime.now()
                    )


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

    def upload_photo(self, photo_path: str, caption: str = "", location_pk: Optional[int] = None, **kwargs: Any) -> IgPost:
        """
        Uploads a single photo to Instagram.

        Args:
            photo_path (str): The path to the photo file.
            caption (str, optional): The caption for the photo. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.
            **kwargs: Additional keyword arguments (hashtags, mentions).

        Returns:
            IgPost: An object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the photo file is not found.
            ClientError: If there's an error from the Instagram API.
        """
        return self._upload_media(
            self.client.photo_upload, 
            "photo", 
            photo_path, 
            caption=caption, 
            location_pk=location_pk, 
            **kwargs
        )

    def upload_video(self, video_path: str, caption: str = "", location_pk: Optional[int] = None, **kwargs: Any) -> IgPost:
        """
        Uploads a video (or Reel without music) to Instagram.

        Args:
            video_path (str): The path to the video file.
            caption (str, optional): The caption for the video/Reel. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.
            **kwargs: Additional keyword arguments (hashtags, mentions).

        Returns:
            IgPost: An object containing information about the uploaded video/Reel.

        Raises:
            FileNotFoundError: If the video file is not found.
            ClientError: If there's an error from the Instagram API.
        """
        return self._upload_media(
            self.client.video_upload, 
            "reel", 
            video_path, 
            caption=caption, 
            location_pk=location_pk, 
            **kwargs
        )

    def upload_album(self, paths: List[str], caption: str = "", location_pk: Optional[int] = None, **kwargs: Any) -> IgPost:
        """
        Uploads a carousel/album post to Instagram.

        Args:
            paths (List[str]): A list of paths to photo and/or video files.
            caption (str, optional): The caption for the album. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.
            **kwargs: Additional keyword arguments (hashtags, mentions).

        Returns:
            IgPost: An object containing information about the uploaded album.

        Raises:
            FileNotFoundError: If any of the media files are not found.
            ClientError: If there's an error from the Instagram API.
        """
        return self._upload_media(
            self.client.album_upload,
            "album",
            paths,
            caption=caption,
            location_pk=location_pk,
            **kwargs
        )

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