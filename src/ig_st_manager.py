"""
ig_st_manager.py
Instagram Story Manager
"""

from ig_client import IgClient
from ig_utils import IgUtils

from instagrapi import Client
from instagrapi.types import (
    StoryBuild, StoryLink, StoryMention,
    StoryMedia, StoryHashtag, StoryLocation, Story, UserShort, Hashtag
)
from instagrapi.exceptions import ClientError


from typing import List, Union, Optional, Tuple, Dict
from pathlib import Path
import logging

#Get the logger
logger = logging.getLogger(__name__)


from ig_data import IgPostData, IgStData



class IgStManager:
    """
    Instagram Story Manager
    """

    def __init__(self, igcl: IgClient, ig_utils: IgUtils) -> None:
        """
        Initializes the Story Manager with an IgClient instance.

        Args:
            igcl (IgClient): The IgClient instance to use for Instagram interactions.
        """
        self.client = igcl.client
        self.ig_utils = ig_utils



    def upload_reel_to_story(
        self,
        reel_url: str,
        caption: str = "",
        mentions: Optional[str] = None,
        location_id: Optional[int] = None,
        hashtags: Optional[str] = None,
        link: Optional[str] = None,
        element_positions: Optional[Dict[str, Tuple[float, float, float, float]]] = None,
        element_rotations: Optional[Dict[str, float]] = None,
        media_x: float = 0.5,
        media_y: float = 0.5,
        media_width: float = 0.5,
        media_height: float = 0.8,
        media_rotation: float = 0.0,
    ) -> Optional[IgStData]:
        """
        Uploads a reel to Instagram Story with user-friendly inputs.

        Args:
            reel_url: URL of the reel to upload.
            caption: Caption for the story.
            mentions: String of comma-separated usernames to mention (e.g., "@user1,@user2").
            location_id: ID of the location to tag.
            hashtags: String of comma-separated hashtags (e.g., "#tag1,#tag2").
            link: URL to attach to the story.
            element_positions: Dictionary mapping element types (mentions, hashtags, links) to their positions (x, y, width, height).
            element_rotations: Dictionary mapping element types to their rotation angles.
            media_x, media_y, media_width, media_height, media_rotation: Positioning and rotation parameters for the reel media.

        Returns:
            IgStData object if upload is successful, otherwise None.
        """
                # Default element positions and rotations
        default_element_positions = {
            "mentions": (0.3, 0.3, 0.7, 0.15),
            "hashtags": (0.2, 0.8, 0.7, 0.15),
            "links": (0.5, 0.5, 0.5, 0.2),  # You can customize this default
        }
        default_element_rotations = {
            "mentions": 0.0,
            "hashtags": 0.0,
            "links": 0.0,
        }

        # Use default positions and rotations if not provided
        element_positions = element_positions or default_element_positions
        element_rotations = element_rotations or default_element_rotations

        print(f"Uploading reel to story: {reel_url}")
        print(type(self.client))

        try:
            media_pk = self.client.media_pk_from_url(reel_url)
            media_path = self.client.video_download(media_pk)

            print(type(media_path))
            print(f"media_pk: {media_pk}")
            print(f"media_path: {media_path}")

            # Create Story elements from user input
            story_mentions = []
            if mentions:
                usernames = (
                    [mentions.lstrip("@")]
                    if "," not in mentions
                    else [m.strip()[1:] for m in mentions.split(",")]
                )
                print(f"usernames: {usernames}")
                print(type(usernames))
                for username in usernames:
                    user_id = self.ig_utils.get_user_id_from_username(username)
                    if user_id:
                        x = element_positions.get("mentions", {}).get("x")
                        y = element_positions.get("mentions", {}).get("y")
                        width = element_positions.get("mentions", {}).get("width")
                        height = element_positions.get("mentions", {}).get("height")
                        story_mentions.append(
                            StoryMention(
                                user=UserShort(pk=user_id, username=username),
                                x=x,
                                y=y,
                                width=width,
                                height=height,
                                rotation=element_rotations.get("mentions"),
                            )
                        )
            print(f"story_mentions: {story_mentions}")
            print(f"story mentions type: {type(story_mentions)}")

            story_hashtags = []
            if hashtags:
                # Split the hashtags string and create Hashtag objects
                for hashtag in hashtags.split(","):
                    hashtag = hashtag.strip().lstrip("#")  # Remove whitespace and "#"
                    story_hashtags.append(
                        StoryHashtag(
                            hashtag=Hashtag(id=hashtag, name=hashtag),  # Create Hashtag object directly
                            x=element_positions.get("hashtags", {}).get("x"),
                            y=element_positions.get("hashtags", {}).get("y"),
                            width=element_positions.get("hashtags", {}).get("width"),
                            height=element_positions.get("hashtags", {}).get("height"),
                            rotation=element_rotations.get("hashtags"),
                        )
                    )

            print(f"story_hashtags: {story_hashtags}")
            print(f"story hashtags type: {type(story_hashtags)}")


            # story_links = StoryLink(link)
            # print(f"story_links: {story_links}")
            # print(f"story links type: {type(story_links)}")

            story_links = []
            if link:
               story_links.append(StoryLink(webUri=link, **(element_positions.get("links", {})), rotation=element_rotations.get("links")))
            print(f"story_links: {story_links}")
            print(f"story links type: {type(story_links)}")


            # Use helper function to get the StoryLocation list
            story_location = []
            if location_id:
                location = self.client.location_info(location_id)  # Get Location object
                story_locations = [
                    StoryLocation(location=location)
                ]  # Create a list with StoryLocationclient.location_info(location_id)

            print(f"story_location: {story_location}")
            print(f"story location type: {type(story_location)}")
            
            print("________________________")
            print("media_path type",type(media_path))
            print(media_path)
            print("caption type")
            print(type(caption))
            print("mentions type", type(mentions))
            print("story_location type",type(story_location), story_location)
            print("story_links",type(story_links), story_links)
            print("story_hashtags",type(story_hashtags), story_hashtags)

            print("media_x",media_x, type(media_x))
            print("media_y",media_y,type(media_y))
            print("media_width",media_width,type(media_width))
            print("media_height",media_height,type(media_height))
            print("media_rotation",media_rotation,type(media_rotation))


            # Upload story
            story_video = self.client.video_upload_to_story(
                media_path,
                caption=caption,
                mentions=story_mentions,
                locations=story_location,
                links=story_links,
                hashtags=story_hashtags,
                medias = [StoryMedia(media_pk=media_pk, x=media_x, y=media_y,
                                     width=media_width, height=media_height,
                                     rotation=media_rotation
                                     )
                          ]
            )

            print(f"story_video: {story_video}")
            print(f"story video type: {type(story_video)}")


          
            # return IgStData object


            return IgStData(
                reel_url=reel_url,
                caption=caption,
                mentions=mentions,
                location_id=location_id,
                hashtags=hashtags,
                link=link,
                pk=story_video.pk,
                id=story_video.id,
                code=story_video.code,
                taken_at=story_video.taken_at
            )

        except Exception as e:
            logger.error(f"Error uploading reel to story: {e}")
            return None


#  PENDING  ->  AAdd methods for uploading videos, creating text stories, adding filters, etc.