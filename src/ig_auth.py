"""
ig_auth.py:
Handles initial authentication with Instagram to create a session file for future interactions.
NEVER commit the session file to version control (add it to your .gitignore).
"""
import os
from instagrapi import Client

def authenticate_and_save_session(session_file="cl_ig.pkl"):
    """
    Authenticates with Instagram using system environment variables for credentials
    and saves the session to a file.
    """
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")

    if not username or not password:
        raise ValueError("IG_USERNAME and IG_PASSWORD must be set as system environment variables.")

    cl = Client()
    cl.login(username, password)

    print("Connected Successfully!")
    cl.dump_settings(session_file)

