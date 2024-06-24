"""
ig_client.py:
Manages the connection to Instagram using Instagrapi, loading the saved session for easy interaction.
"""
import os
from instagrapi import Client
from instagrapi.types import StoryHashtag, StoryLink, StoryMention, StorySticker 

class IgClient:
    """ We've added a check at the beginning to see if the session file exists.
    If it doesn't, we raise a FileNotFoundError to prompt the user to authenticate.
    This prevents errors if the user tries to create a client without having authenticated first.
    """
    
    def __init__(self, session_file="cl_ig.pkl"):
        self.client = Client()

        if not os.path.exists(session_file):
            raise FileNotFoundError("Session file not found. Please authenticate first.")

        try:
            self.client.load_settings(session_file)
        except Exception as e: 
            raise Exception(f"An error occurred loading the session file: {e}")

    def get_user_id(self, username):
        try:
            user_info = self.client.user_info_by_username(username)
            return user_info.pk
        except Exception as e: 
            raise Exception(f"An error occurred fetching user ID: {e}")
