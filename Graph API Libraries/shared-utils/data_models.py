# shared_utils/data_models.py 

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class SocialMediaPost:
    platform: str         # 'FB', 'IG', 'TH', 'TT', 'YT', 'X'
    post_id: str
    message: str          # Caption or text content
    author: str          # Username or ID of the author
    timestamp: datetime   # Date and time the post was created
    media_type: List[str] = field(default_factory=list)  # 'photo', 'video', 'carousel' (IG), 'short', 'long' (YT)
    media_urls: List[str] = field(default_factory=list)
    likes: int = 0
    comments: int = 0
    shares: int = 0        # For Facebook posts
    permalink_url: Optional[str] = None  # Permanent link to the post

    # Additional fields for potential features:
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)

    # Media dimensions (optional, if applicable):
    media_width: Optional[int] = None
    media_height: Optional[int] = None
    # ... (Other platform-specific fields as needed)


@dataclass
class Comment:
    comment_id: str
    post_id: str         # ID of the post this comment belongs to
    text: str
    author: str
    timestamp: datetime
    likes: int = 0
    replies: int = 0      # Number of replies to this comment

    # Additional fields for potential features:
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
