from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from instagrapi.types import (
    StoryMention,
    StoryMedia,
    StoryLink,
    StoryHashtag,
    StoryLocation,
    StorySticker,
    UserShort,
    HttpUrl,
)


@dataclass
class IgPostData:
    """Represents an Instagram post (or reel) with relevant data.

    Attributes:
        media_id (str): The unique identifier of the post/reel.
        media_type (int): The type of media (1: Photo, 2: Video/IGTV/Reel, 8: Album).
        product_type (str): The type of video content ("feed", "igtv", "clips").
        caption (str): The post caption, potentially including hashtags and mentions.
        timestamp (datetime): The date and time the post was created.
        media_url (str, optional): URL of the media (not relevant for albums).
        location_pk (int, optional): Location ID (primary key).
        location_name (str, optional): Name of the location.
        like_count (int): The number of likes (default: 0).
        comment_count (int): The number of comments (default: 0).
        is_album (bool): Indicates whether the post is an album (default: False).
        album_media_ids (List[str], optional): List of media IDs in the album (if it's an album).
        album_media_urls (List[str], optional): List of media URLs in the album (if it's an album).
    """

    media_id: str
    media_type: int
    product_type: Optional[str]
    caption: str  # complete with hashtags and mentions
    timestamp: datetime
    media_url: Optional[str] = None  # Might not be relevant for albums
    location_pk: Optional[int] = None
    location_name: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    is_album: bool = False
    album_media_ids: Optional[List[str]] = None  # List of media IDs in the album
    album_media_urls: Optional[List[str]] = None  # List of media URLs in the album


1. Revised IgReelData

Python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from instagrapi.types import (
    StoryMention,
    StoryMedia,
    StoryLink,
    StoryHashtag,
    StoryLocation,
    StorySticker,
    UserShort,
    HttpUrl,
)

@dataclass
class IgReelData:
    """Represents an Instagram Reel with relevant data.

    Attributes:
        media_id (str): The unique identifier of the reel.
        caption (str): The reel's caption, potentially including hashtags and mentions.
        timestamp (datetime): The date and time the reel was created.
        media_url (str): URL of the reel video.
        thumbnail_url (str): URL of the reel's thumbnail image.
        location_pk (int, optional): Location ID (primary key).
        location_name (str, optional): Name of the location.
        like_count (int): The number of likes (default: 0).
        comment_count (int): The number of comments (default: 0).
        audio_track (str, optional): Name of the audio track used in the reel.
        effects (List[str], optional): List of effects used in the reel.
        duration (int): Duration of the reel in seconds.
    """

    media_id: str
    caption: str  # complete with hashtags and mentions
    timestamp: datetime
    media_url: str 
    thumbnail_url: str
    location_pk: Optional[int] = None
    location_name: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    audio_track: Optional[str] = None
    effects: Optional[List[str]] = field(default_factory=list)
    duration: int = 0 
@dataclass
class IgStData:
    """Represents essential data for an Instagram story.

    Attributes:
        pk (int): The unique identifier of the story (primary key).
        id (str): A unique ID for the story (different from pk).
        code (str): A shortcode for the story.
        taken_at (datetime): The date and time the story was created.
        reel_url (str): The URL of the story reel.
        caption (str, optional): The story caption (default: "").
        mentions (List[str], optional): List of mentioned users (default: empty list).
        location_id (int, optional): The ID of the location tagged in the story.
        hashtags (List[str], optional): List of hashtags used in the story (default: empty list).
        link (str, optional): A link included in the story.
    """

    # Parameters extracted from StoryObject (no default values)
    pk: int
    id: str
    code: str
    taken_at: datetime

    # User-provided parameters (some have default values)
    reel_url: str
    caption: str = ""
    mentions: Optional[List[str]] = field(default_factory=list)
    location_id: Optional[int] = None
    hashtags: Optional[List[str]] = field(default_factory=list)
    link: Optional[str] = None

    # Additional fields you might want to add
    # e.g., is_paid_partnership: bool = False
    #       imported_taken_at: Optional[datetime] = None


@dataclass
class IgCommentData:
    """
    Represents an Instagram comment with detailed information.

    Attributes:
        comment_id (int): The unique identifier of the comment.
        post_id (int): The ID of the post the comment belongs to.
        user_id (int): The ID of the user who made the comment.
        comment_text (str): The text content of the comment.
        timestamp (datetime): The date and time the comment was created.
        reply_to_comment_id (Optional[int]): The ID of the parent comment
                                            (if it's a reply).
        status (str): The status of the comment ('active', 'deleted', 'replied').
        user_name (Optional[str]): The username of the commenter.
        user_full_name (Optional[str]): The full name of the commenter.
        is_business_account (Optional[bool]): Whether the commenter is a
                                             business account.
    """

    comment_id: int
    post_id: int
    user_id: int
    comment_text: str
    timestamp: datetime
    reply_to_comment_id: Optional[int] = None
    status: str = "active"
    user_name: Optional[str] = None
    user_full_name: Optional[str] = None
    is_business_account: Optional[bool] = None
