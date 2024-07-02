from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from instagrapi.types import Location, Media

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
    
    # Add other relevant attributes as needed (avoid complex objects)
