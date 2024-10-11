import sys
import os
from typing import Optional, Tuple, List, Any, Dict
import datetime

from fb_post_tracker import FbPostTracker


def process_row(row_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process the row data and prepare it for writing back to the spreadsheet.

    Args:
        row_data (Dict[str, Any]): The data from the unpublished row.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing the published data and the data for the published tab.
    """
    current_datetime = datetime.datetime.now()
    published_data = {
        "Published? Y/N": "Y",
        "Date and Time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "ID (str.)": "PLACEHOLDER_ID",
    }
    published_tab_data = {
        "Ref #": row_data.get("#", ""),
        "Subject": row_data.get("Subject", ""),
        "Type": row_data.get("Type", ""),
        "Published? Y/N": "Y",
        "Date and Time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "ID (str.)": "PLACEHOLDER_ID",
    }
    return published_data, published_tab_data


def simulate_publishing(post_type: str, post_data: Dict[str, Any]) -> str:
    """
    Simulate publishing a post based on its type.

    Args:
        post_type (str): The type of the post.
        post_data (Dict[str, Any]): The post data.

    Returns:
        str: A simulated post ID.
    """
    print(f"Simulating publishing of {post_type} post:")
    print(f"  Content: {post_data.get('Post comment', '')}")
    print(f"  Media: {post_data.get('Media Souce links separated by comma', '')}")
    return f"SIMULATED_POST_ID_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"


def main():
    account_id = "JK"
    spreadsheet_id = "1wrvG3wmptA76kywbVe1gy5as-ALDzmebLvqoxWIw9mw"

    try:
        tracker = FacebookPostTracker(account_id, spreadsheet_id)
    except ValueError as e:
        print(f"Error initializing FacebookPostTracker: {e}")
        return

    post_data = tracker.get_next_unpublished_post()
    if post_data is None:
        print("No unpublished posts to process.")
        return

    row_index = post_data["row_index"]
    print(f"\nProcessing row {row_index}:")
    print("-" * 40)
    for key, value in post_data.items():
        print(f"{key}: {value}")
    print("-" * 40)

    post_type = post_data.get("Type", "").lower()
    post_id = simulate_publishing(post_type, post_data)

    if post_id:
        published_data, published_tab_data = process_row(post_data)
        published_data["ID (str.)"] = post_id
        published_tab_data["ID (str.)"] = post_id

        tracker.mark_post_as_published(row_index, post_id)
        tracker.add_post_to_published_log(published_tab_data)
        print(
            f"Successfully simulated publishing of {post_type} post with ID: {post_id}"
        )
    else:
        print(f"Failed to simulate publishing of {post_type} post")
        tracker.update_post_status(row_index, "Failed")

    print("Processing completed successfully.")


if __name__ == "__main__":
    main()
