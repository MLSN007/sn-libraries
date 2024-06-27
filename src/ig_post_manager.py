"""
ig_post_manager.py:
Facilitates the creation and management of various types of Instagram posts (photos, videos, albums/carousels).
"""
import os
import time, datetime
import logging
from typing import List, Dict, Any
from instagrapi import Client
from instagrapi.exceptions import ClientError
from instagrapi.types import Location, StoryHashtag, StoryLink, StoryMention, StorySticker
from ig_client import IgClient
from ig_data import IgPost


class IgPostManager:
    """Handles Instagram post operations using the IgClient."""

    def __init__(self, insta_client: IgClient):
        """
        Initializes the PostManager with an IgClient instance.

        Args:
            insta_client: The IgClient instance to use for Instagram interactions.
        """
        self.client = insta_client.client

    def _upload_media(self, upload_func, media_type, *args, max_retries=3, retry_delay=5, **kwargs):
        """
        Generic helper function to upload media (photo, video, album) with retries.
        """
        retries = 0
        while retries < max_retries:
            try:
                media = upload_func(*args, **kwargs)
                return IgPost(
                    media_id=media.pk,
                    media_type=media_type,
                    caption=kwargs.get('caption', ''),
                    timestamp=media.taken_at,
                    location=media.location,
                    like_count=media.like_count,
                    comment_count=media.comment_count,
                    published=True,
                    tags=kwargs.get('hashtags', []),  
                    mentions=kwargs.get('mentions', []) 
                )
            except (FileNotFoundError, ClientError) as e:
                logging.error(f"Error during {media_type} upload (attempt {retries + 1}/{max_retries}): {e}")
                retries += 1
                if retries < max_retries:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)  # Wait before retrying
                else:
                    # Maximum retries reached, mark as failed
                    return IgPost(
                        published=False,
                        failed_attempts=retries,
                        last_failed_attempt=datetime.datetime.now()
                    )


    def _add_tags_and_mentions_to_caption(self, caption, hashtags, mentions):
        """Adds hashtags and mentions to the caption."""
        caption_with_tags = caption + " " + " ".join(hashtags) if hashtags else caption
        caption_with_mentions = caption_with_tags + " " + " ".join([f"@{m}" for m in mentions]) if mentions else caption_with_tags
        return caption_with_mentions


    def upload_photo(self, photo_path: str, caption: str = "", location_pk: int = None, 
                    hashtags: List[str] = None, mentions: List[str] = None) -> IgPost:
        """
        Uploads a single photo to Instagram.

        Args:
            photo_path (str): The path to the photo file.
            caption (str, optional): The caption for the photo. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.
            hashtags (List[str], optional): List of hashtags to add to the caption. Defaults to None.
            mentions (List[str], optional): List of usernames to mention in the caption. Defaults to None.

        Returns:
            IgPost: An object containing information about the uploaded post.

        Raises:
            FileNotFoundError: If the photo file is not found.
            ClientError: If there's an error from the Instagram API.
        """
        # Add hashtags and mentions to caption
        caption = self._add_tags_and_mentions_to_caption(caption, hashtags, mentions)
        
        # If location_pk is provided, create a Location object
        location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores") if location_pk else None

        return self._upload_media(
            self.client.photo_upload, 
            "photo", 
            photo_path, 
            caption=caption, 
            location=location, 
            hashtags=hashtags, 
            mentions=mentions
        )



    def upload_video(self, video_path: str, caption: str = "", location_pk: int = None, 
                     hashtags: List[str] = None, mentions: List[str] = None) -> IgPost:
        """
        Uploads a video (or Reel without music) to Instagram.

        Args:
            video_path (str): The path to the video file.
            caption (str, optional): The caption for the video/Reel. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.
            hashtags (List[str], optional): List of hashtags to add to the caption. Defaults to None.
            mentions (List[str], optional): List of usernames to mention in the caption. Defaults to None.

        Returns:
            IgPost: An object containing information about the uploaded video/Reel.

        Raises:
            FileNotFoundError: If the video file is not found.
            ClientError: If there's an error from the Instagram API.
        """
        # Add hashtags and mentions to caption
        caption = self._add_tags_and_mentions_to_caption(caption, hashtags, mentions)
        
        # If location_pk is provided, create a Location object
        location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores") if location_pk else None

        return self._upload_media(
            self.client.video_upload, 
            "reel", 
            video_path, 
            caption=caption, 
            location=location, 
            hashtags=hashtags, 
            mentions=mentions
        )

    def upload_album(self, paths: List[str], caption: str = "", location_pk: int = None,
                    hashtags: List[str] = None, mentions: List[str] = None) -> IgPost:
        """
        Uploads a carousel/album post to Instagram with optional caption, location,
        and retry mechanisms for handling errors.

        Args:
            paths (List[str]): A list of paths to photo and/or video files.
            caption (str, optional): The caption for the album. Defaults to "".
            location_pk (int, optional): The location PK to tag in the post. Defaults to None.
            hashtags (List[str], optional): List of hashtags to add to the caption. Defaults to None.
            mentions (List[str], optional): List of usernames to mention in the caption. Defaults to None.


        Returns:
            IgPost: An object containing information about the uploaded album.

        Raises:
            FileNotFoundError: If any of the media files are not found.
            ClientError: If there's an error from the Instagram API.
        """

        # Add hashtags and mentions to caption
        caption = self._add_tags_and_mentions_to_caption(caption, hashtags, mentions)

        # If location_pk is provided, create a Location object
        location = Location(pk=location_pk, name="Malecón Cisneros - Miraflores") if location_pk else None
        return self._upload_media(
            self.client.album_upload,
            "album",
            [self.client.photo_upload(p, caption) for p in paths if p.endswith((".jpg", ".jpeg", ".png"))] + 
            [self.client.video_upload(p, caption) for p in paths if p.endswith((".mp4", ".mov"))],
            caption=caption,
            location=location,
            hashtags=hashtags, mentions=mentions
        )



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