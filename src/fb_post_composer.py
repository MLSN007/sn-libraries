import os
from typing import Dict, Any, List

class FbPostComposer:
    def __init__(self, source_path: str):
        self.source_path = source_path

    def compose_message(self, post_data: Dict[str, Any]) -> str:
        """Compose the message for the post."""
        message = post_data.get('Post comment', '')
        hashtags = post_data.get('hashtags separated by blank', '')
        mentions = post_data.get('mentions separated by blank', '')

        if hashtags:
            message += f"\n\n{hashtags}"
        if mentions:
            message += f"\n\n{mentions}"

        return message.strip()

    def get_media_paths(self, post_data: Dict[str, Any]) -> List[str]:
        """Get the full paths of media files."""
        media_sources = post_data.get('Media Souce links separated by comma', '').split(',')
        return [os.path.join(self.source_path, source.strip()) for source in media_sources if source.strip()]

    def get_media_titles(self, post_data: Dict[str, Any]) -> List[str]:
        """Get the titles of media files."""
        return [title.strip() for title in post_data.get('titles of media source separated by comma', '').split(',') if title.strip()]
