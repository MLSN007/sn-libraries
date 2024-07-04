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
    HttpUrl
)
from instagrapi.story import StoryBuilder

@dataclass
class IgPostData:
    """represents and Instagram post or reel with relevant data

    Media types:
        Photo - When media_type=1
        Video - When media_type=2 and product_type=feed
        IGTV - When media_type=2 and product_type=igtv
        Reel - When media_type=2 and product_type=clips
        Album - When media_type=8
    """
    media_id: str
    media_type: int
    product_type: Optional[str]
    caption: str                        # complete with hashtags and mentions
    timestamp: datetime
    media_url: Optional[str] = None  # Might not be relevant for albums
    location_pk: Optional[int] = None
    location_name: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    is_album: bool = False
    album_media_ids: Optional[List[str]] = None  # List of media IDs in the album
    album_media_urls: Optional[List[str]] = None  # List of media URLs in the album

@dataclass
class IgStData:
    """Represents essential data for an Instagram story (reel)."""

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



# Add other relevant attributes as needed (avoid complex objects)
