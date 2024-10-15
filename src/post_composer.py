import os
from typing import List


class PostComposer:
    def __init__(self, source_path: str):
        self.source_path = source_path

    def compose_message(self, post_data: dict) -> str:
        print("Composing message for the post")
        message = post_data.get("Post comment", "").strip()
        hashtags = post_data.get("hashtags separated by blank", "").strip()
        mentions = post_data.get("mentions separated by blank", "").strip()

        if hashtags:
            message += f"\n\n{hashtags}"
        if mentions:
            message += f"\n\n{mentions}"

        print(f"Composed message: {message[:50]}...")  # Print first 50 characters
        return message

    def get_media_paths(self, post_data: dict) -> List[str]:
        print("Getting media paths")
        media_sources = post_data.get("Media Souce links separated by comma", "")
        paths = [
            os.path.join(self.source_path, path.strip())
            for path in media_sources.split(",")
            if path.strip()
        ]
        print(f"Media paths: {paths}")
        return paths

    def get_media_titles(self, post_data: dict) -> List[str]:
        print("Getting media titles")
        media_titles = post_data.get("titles of media source separated by comma", "")
        titles = [title.strip() for title in media_titles.split(",") if title.strip()]
        print(f"Media titles: {titles}")
        return titles
