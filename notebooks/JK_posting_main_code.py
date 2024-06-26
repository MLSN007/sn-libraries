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
from ig_auth import authenticate_and_save_session
from ig_client import IgClient
from ig_data import IgPost, create_post_dataframe
from ig_post_manager import IgPostManager
from config import POSTS_HISTORY_FILE


def publish_post(post_manager: IgPostManager, row: pd.Series):
    """
    Publishes a post based on the data in the row.
    """
    post_type = row["post_type"].lower()
    media_path = row["Video/photo path"]
    caption = row["Caption"]
    hashtags = row["Hastags"].split(',') if not pd.isna(row["Hastags"]) else []
    mentions = row["Mentions"].split(',') if not pd.isna(row["Mentions"]) else []

    if post_type == "photo":
        return post_manager.upload_photo(media_path, caption, hashtags=hashtags, mentions=mentions)
    elif post_type == "video":
        return post_manager.upload_reel(media_path, caption, hashtags=hashtags, mentions=mentions)
    elif post_type == "album":
        media_paths = media_path.split(",")
        return post_manager.upload_album(media_paths, caption, hashtags=hashtags, mentions=mentions)
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
    df_posts = pd.read_excel("your_excel_file.xlsx")  # Update with your file path

    # Load existing post history and combine with new data
    df_posts = load_and_merge_post_history(df_posts)

    # Schedule posts
    published_posts = []
    for _, row in df_posts[df_posts['published'] == False].head(2).iterrows():
        try:
            post = publish_post(post_manager, row)
            if post.published: #Add to the list only if published successfully
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
            

if __name__ == "__main__":
    main()
