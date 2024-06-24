"""
ig_post_manager.py:
Facilitates the creation and management of various types of
Instagram posts (photos, videos, albums/carousels)
including the ability to add music to videos.
"""

from ig_client import IgClient # Note the updated import path

class IgPostManager:  
    def __init__(self, insta_client: IgClient):
        """
        Initializes the PostManager with an IgClient instance.

        Args:
            insta_client: The IgClient instance to use for Instagram interactions.
        """
        self.client = insta_client.client

    def upload_photo(self, photo_path, caption=""):
        try:
            return self.client.photo_upload(photo_path, caption=caption)
        except Exception as e:
            raise Exception(f"Error uploading photo: {e}")

    def upload_video(self, video_path, caption=""):
        try:
            return self.client.video_upload(video_path, caption=caption)
        except Exception as e:
            raise Exception(f"Error uploading video: {e}")

    def upload_album(self, paths, caption=""):
        try:
            media = []
            for path in paths:
                if path.endswith((".jpg", ".jpeg", ".png")):
                    media.append(self.client.photo_upload(path))
                elif path.endswith((".mp4", ".mov")):
                    media.append(self.client.video_upload(path))
            return self.client.album_upload(media, caption=caption)
        except Exception as e:
            raise Exception(f"Error uploading album: {e}") from e


    def upload_video_with_music(self, video_path, music_path, caption=""):
        """
        Uploads a video to Instagram with a specified music track and an optional caption.

        Args:
            video_path: The path to the video file.
            music_path: The path to the music file (supported formats: .mp3, .m4a).
            caption: (Optional) The caption for the video.

        Returns:
            The Instagrapi Media object representing the uploaded video with music.
        """

        try:
            return self.client.video_upload(video_path, caption=caption, audio_path=music_path)
        except Exception as e:
            raise Exception(f"Error uploading video with music: {e}")

    def search_music(self, query):
        """
        Searches for music tracks on Instagram based on a query.

        Args:
            query: The search query for music.

        Returns:
            A list of MusicTrack objects matching the query.
        """
        try:
            return self.client.music_search(query)
        except Exception as e:
            raise Exception(f"Error searching for music: {e}")

    def upload_reel_with_music(self, video_path, music_track_id, caption=""):
        """
        Uploads a Reel to Instagram with a specified music track ID and an optional caption.
        (Note: Reel-specific features like effects are not yet implemented.)

        Args:
            video_path: The path to the video file.
            music_track_id: The ID of the music track to use (obtained from `search_music`).
            caption: (Optional) The caption for the Reel.

        Returns:
            The Instagrapi Media object representing the uploaded Reel.
        """
        try:
            return self.client.clip_upload(video_path, caption=caption, music_id=music_track_id)
        except Exception as e:
            raise Exception(f"Error uploading Reel with music: {e}")
