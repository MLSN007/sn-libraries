"""
main.py:
Schedules and publishes Instagram posts from an Excel spreadsheet,
managing post history and retrying failed uploads.
"""

import os
import json
import random
import time
import datetime
import logging

import pandas as pd
import openpyxl

from ig_auth import authenticate_and_save_session
from ig_client import IgClient
from ig_data import IgPost, create_post_dataframe
from ig_post_manager import IgPostManager
from ig_config import POSTS_HISTORY_FILE


def publish_post(post_manager: IgPostManager, row: pd.Series):
    """
    Publishes a post based on the data in the row.
    """
    post_type = row["post_type"].lower()
    media_path = row["Video/photo path"]
    caption = row["Caption"]
    hashtags = row["Hashtags"]
    mentions = row["Mentions"]

    location_pk = row.get("Location")  # Get location PK from the row

    if location_pk:
        try:
            # Fetch location details from Instagram using the PK
            location = post_manager.client.location_complete_info(location_pk).location
        except ClientError as e:
            logging.error(f"Error getting location info for PK {location_pk}: {e}")
            location = None  # Set location to None if there's an error
    else:
        location = None

    if post_type == "photo":
        return post_manager.upload_photo(media_path, caption, location, hashtags=hashtags, mentions=mentions)
    elif post_type == "video":
        return post_manager.upload_video(media_path, caption, location, hashtags=hashtags, mentions=mentions)
    elif post_type == "album":
        media_paths = media_path.split(",")
        return post_manager.upload_album(media_paths, caption, location, hashtags=hashtags, mentions=mentions)
    else:
        raise ValueError(f"Invalid post type: {post_type}")


def load_and_merge_post_history(new_posts_df):
    """
    Loads existing post history from a JSON file, merges it with new posts,
    and returns the combined DataFrame.
    """

    if os.path.exists(POSTS_HISTORY_FILE):
        with open(POSTS_HISTORY_FILE, "r", encoding="utf-8") as f:
            existing_posts = json.load(f).get("posts", [])
        existing_df = create_post_dataframe(
            [IgPost(**post_data) for post_data in existing_posts]
        )
        df_posts = pd.concat([existing_df, new_posts_df], ignore_index=True)
    else:
        df_posts = new_posts_df
        df_posts["published"] = False
        df_posts["failed_attempts"] = 0
        df_posts["last_failed_attempt"] = None

    return df_posts
        

def main():
    # 1. Authentication (Always attempt authentication first)
    session_file = "cl_ig.pkl"
    if not os.path.exists(session_file):  # Check if session file exists
        authenticate_and_save_session(session_file)

    # Now, you should have a valid session, so create the client
    insta_client = IgClient(session_file)
    post_manager = IgPostManager(insta_client)

    # Read Excel into DataFrame
    df_posts = pd.read_excel(r"C:\Users\manue\Documents\GitHubMLSN\sn-libraries\notebooks\JK_post_in_queue.xlsx")

    # Check if 'published' column exists in the DataFrame
    if 'published' not in df_posts.columns:
        df_posts["published"] = False

    # Load existing post history and combine with new data
    df_posts = load_and_merge_post_history(df_posts)


pprint(df_posts)


    # Schedule posts
    published_posts = []
    df_posts['failed_attempts'] = 0  # Initialize 'failed_attempts' column here

    for _, row in df_posts[df_posts['published'] == False].head(2).iterrows():
        try:
            post = publish_post(post_manager, row)
            if post.published:  # Add to the list only if published successfully
                published_posts.append(post.to_dict())
            else:
                # If failed, update the DataFrame with failed attempts and timestamp
                df_posts.loc[df_posts['post_id'] == row['post_id'], 'failed_attempts'] = post.failed_attempts
                df_posts.loc[df_posts['post_id'] == row['post_id'], 'last_failed_attempt'] = post.last_failed_attempt

            time.sleep(random.randint(90, 900))
        except Exception as e:
            # Handle errors (log, retry, skip, or stop)
            logging.error(f"Error publishing post: {e}")
            row['published'] = False
            row['failed_attempts'] += 1
            row['last_failed_attempt'] = datetime.datetime.now()

print("solo queda guardar el historico en algun sitio")
import pprint
pprint.pprint(published_posts)


    #Update Posts History
    if os.path.exists(POSTS_HISTORY_FILE):
        with open(POSTS_HISTORY_FILE, "r", encoding="utf-8") as f:
            posts_data = json.load(f)
        posts_data["posts"].extend(published_posts)
        with open(POSTS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=4)
    else: 
        posts_data = {"posts": published_posts}
        with open(POSTS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=4)

    #Update Posts History
    if os.path.exists(POSTS_HISTORY_FILE):
        with open(POSTS_HISTORY_FILE, "r", encoding="utf-8") as f:
            posts_data = json.load(f)
        posts_data["posts"].extend(published_posts)
        with open(POSTS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=4)
    else: 
        posts_data = {"posts": published_posts}
        with open(POSTS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=4)
            
# ------------------MAIN ------------


if __name__ == "__main__":
    main()
   
# ------------------ TESTS -------------------
# 1. Test Authentication
def test_authentication():
    """Tests the authentication process and saves the session."""
    session_file = "cl_ig.pkl"
    if not os.path.exists(session_file):
        authenticate_and_save_session(session_file)
    print("Authentication successful!")

# 2. Test IgClient and IgPostManager
def test_client_and_manager():
    """Tests the IgClient and IgPostManager by creating a dummy post."""
    session_file = "cl_ig.pkl"
    insta_client = IgClient(session_file)
    post_manager = IgPostManager(insta_client)
    dummy_post = IgPost(media_id="dummy_post", media_type="photo",
                        caption="Dummy caption", tags=["dummy", "hashtag"], mentions=["dummy", "mention"])
    print(f"Dummy post created: {dummy_post}")

# 3. Test publish_post
def test_publish_post():
    """Tests the publish_post function with a dummy post."""
    session_file = "cl_ig.pkl"
    insta_client = IgClient(session_file)
    post_manager = IgPostManager(insta_client)
    dummy_row = pd.Series({"post_type": "photo",
                           "Video/photo path": "dummy_path",
                           "Caption": "Dummy caption",
                           "Tags": "#NurserySchoolParty #Parade #CulturalFestivity",
                           "Mentions": "dummy,mention", "media_id": "dummy_media_id"})

    try:
        post = publish_post(post_manager, dummy_row)
        print(f"Post published successfully: {post}")
    except Exception as e:
        print(f"Error publishing post: {e}")

# 4. Test load_and_merge_post_history
def test_load_and_merge_post_history():
    """Tests the load_and_merge_post_history function with a dummy DataFrame."""
    dummy_df = pd.DataFrame({"post_id": ["dummy_post"], "post_type": ["photo"], "Video/photo path": ["dummy_path"], "Caption": ["Dummy caption"], "Hashtags": ["dummy,hashtag"], "Mentions": ["dummy,mention"]})
    merged_df = load_and_merge_post_history(dummy_df)
    print(f"Merged DataFrame: {merged_df}")

# 5. Run main step by step
def run_main_step_by_step():
    """Runs the main function step by step, allowing for debugging and inspection."""
    # 1. Authentication (Always attempt authentication first)
    session_file = "cl_ig.pkl"
    if not os.path.exists(session_file):  # Check if session file exists
        authenticate_and_save_session(session_file)
    print("Authentication successful!")

    # Now, you should have a valid session, so create the client
    insta_client = IgClient(session_file)
    post_manager = IgPostManager(insta_client)

    # Read Excel into DataFrame
    df_posts = pd.read_excel("C:\\Users\\manue\\Documents\\GitHubMLSN\\sn-libraries\\notebooks\\JK_post_in_queue.xlsx")   # Update with your file path
    print("Excel file loaded successfully!")

    # Load existing post history and combine with new data
    df_posts = load_and_merge_post_history(df_posts)
    print("Post history loaded and merged!")

    # Schedule posts
    published_posts = []
    for _, row in df_posts[df_posts['published'] == False].head(2).iterrows():
        print(f"Processing row: {row}")
        try:
            post = publish_post(post_manager, row)
            if post.published: #Add to the list only if published successfully
                published_posts.append(post.to_dict())
                print(f"Post published successfully: {post}")
            else:
                # If failed, update the DataFrame with failed attempts and timestamp
                df_posts.loc[df_posts['post_id'] == row['post_id'], 'failed_attempts'] = post.failed_attempts
                df_posts.loc[df_posts['post_id'] == row['post_id'], 'last_failed_attempt'] = post.last_failed_attempt
                print(f"Post failed to publish: {post}")
            
            time.sleep(random.randint(90, 900))
        except Exception as e:
            # Handle errors (log, retry, skip, or stop)
            logging.error(f"Error publishing post: {e}")
            row['published'] = False
            row['failed_attempts'] += 1
            row['last_failed_attempt'] = datetime.datetime.now()
            print(f"Error publishing post: {e}")

    #Update Posts History
    if os.path.exists(POSTS_HISTORY_FILE):
        with open(POSTS_HISTORY_FILE, "r", encoding="utf-8") as f:
            posts_data = json.load(f)
        posts_data["posts"].extend(published_posts)
        with open(POSTS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=4)
        print("Post history updated successfully!")
    else: 
        posts_data = {"posts": published_posts}
        with open(POSTS_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, ensure_ascii=False, indent=4)
        print("Post history created successfully!")

# Choose which test or step-by-step execution you want to run
# test_authentication()
# test_client_and_manager()
# test_publish_post()
# test_load_and_merge_post_history()

# run_main_step_by_step()
