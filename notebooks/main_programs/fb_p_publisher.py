import os
import json
from typing import List, Optional
from fb_post_tracker import FbPostTracker
from fb_post_manager import FbPostManager
from fb_api_client import FbApiClient


def load_fb_config(config_file: str) -> dict:
    """Load the Facebook configuration from a JSON file."""
    print(f"Loading Facebook configuration from: {config_file}")
    with open(config_file, "r") as f:
        config = json.load(f)
    print("Facebook configuration loaded successfully")
    return config


def load_credentials(fb_config: dict) -> dict:
    """Load Facebook credentials from environment variables."""
    print("Loading Facebook credentials from environment variables")
    credentials = {}
    try:
        for key in [
            "app_id",
            "app_secret",
            "access_token",
            "page_id",
            "user_id",
            "user_token",
        ]:
            credentials[key] = os.environ[fb_config[key]]
            print(
                f"Loaded {key}: {credentials[key][:5]}..."
            )  # Print first 5 characters for security
    except KeyError as e:
        print(
            f"Error: Environment variable {e} not set. Please set it before running the script."
        )
        exit(1)
    print("Facebook credentials loaded successfully")
    return credentials


def compose_message(post_data: dict) -> str:
    """Compose the full message for the post."""
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


def get_media_paths(post_data: dict) -> List[str]:
    """Get the list of media paths from the post data."""
    print("Getting media paths")
    media_sources = post_data.get("Media Souce links separated by comma", "")  # Note the typo in "Souce"
    paths = [path.strip() for path in media_sources.split(",") if path.strip()]
    print(f"Media paths: {paths}")
    return paths


def get_media_titles(post_data: dict) -> List[str]:
    """Get the list of media titles from the post data."""
    print("Getting media titles")
    media_titles = post_data.get("titles of media source separated by comma", "")
    titles = [title.strip() for title in media_titles.split(",") if title.strip()]
    print(f"Media titles: {titles}")
    return titles


def main():
    # Load Facebook configuration
    config_file = r"..\config_files\FB_JK_JK Travel_JK Travel_config.json"
    fb_config = load_fb_config(config_file)
    credentials = load_credentials(fb_config)

    # Set up Google Sheets configuration
    account_id = "JK"
    spreadsheet_id = "1wrvG3wmptA76kywbVe1gy5as-ALDzmebLvqoxWIw9mw"
    print(
        f"Google Sheets configuration - Account ID: {account_id}, Spreadsheet ID: {spreadsheet_id}"
    )

    # Initialize the necessary components
    print("Initializing API client, post tracker, and post manager")
    api_client = FbApiClient(credentials)
    tracker = FbPostTracker(account_id, spreadsheet_id)
    fb_post_manager = FbPostManager(api_client)

    # Get the next unpublished post
    print("Getting next unpublished post")
    post_data = tracker.get_next_unpublished_post()
    if not post_data:
        print("No posts to publish")
        return

    print(f"Post data retrieved: {post_data}")

    post_type = post_data.get("Type", "").lower()
    print(f"Post type: {post_type}")

    message = compose_message(post_data)
    media_paths = get_media_paths(post_data)
    media_titles = get_media_titles(post_data)
    post_id: Optional[str] = None

    print(f"Attempting to publish {post_type} post")
    try:
        if post_type == "text":
            post_id = fb_post_manager.publish_text_post(credentials["page_id"], message)
        elif post_type == "single photo":
            if media_paths:
                post_id = fb_post_manager.publish_photo_post(
                    credentials["page_id"], message, media_paths[0]
                )
            else:
                raise ValueError(f"No media path provided for single photo post. Post data: {post_data}")
        elif post_type == "multiple photo":
            post_id = fb_post_manager.publish_multi_photo_post(
                credentials["page_id"], message, media_paths
            )
        elif post_type == "video":
            if media_paths:
                title = media_titles[0] if media_titles else None
                post_id = fb_post_manager.publish_video_post(
                    credentials["page_id"], message, media_paths[0], title
                )
            else:
                raise ValueError("No media path provided for video post")
        elif post_type == "reel":
            if media_paths:
                title = media_titles[0] if media_titles else None
                post_id = fb_post_manager.publish_reel(
                    credentials["page_id"], message, media_paths[0], title
                )
            else:
                raise ValueError("No media path provided for reel post")
        else:
            print(f"Unknown post type: {post_type}")
            return

        if post_id:
            print(f"Successfully published {post_type} post with ID: {post_id}")
            print("Updating spreadsheet with published information")
            tracker.mark_post_as_published(post_data["row_index"], post_id)
            tracker.add_post_to_published_log(post_data)
        else:
            print(f"Failed to publish {post_type} post")
            print("Updating spreadsheet with failure status")
            tracker.update_post_status(post_data["row_index"], "Failed")

    except Exception as e:
        print(f"Error publishing {post_type} post: {str(e)}")
        print(f"Full post data: {post_data}")
        print(f"Media paths: {media_paths}")
        print(f"Media titles: {media_titles}")
        print("Updating spreadsheet with error status")
        tracker.update_post_status(post_data["row_index"], "Error")

    # Add this at the end of the main function for debugging
    print("\nFinal state:")
    print(f"Post type: {post_type}")
    print(f"Message: {message}")
    print(f"Media paths: {media_paths}")
    print(f"Media titles: {media_titles}")


if __name__ == "__main__":
    main()
