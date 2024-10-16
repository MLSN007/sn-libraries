"""Showcase of FbCommentManager functionality."""

import os
import time
import logging
from fb_config_loader import FbConfigLoader
from fb_api_client import FbApiClient
from fb_comment_manager import FbCommentManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    try:
        # Load configuration
        config_file = os.path.join(
            "config_files", "FB_JK_JK Travel_JK Travel_config.json"
        )
        config_loader = FbConfigLoader(config_file)

        # Initialize FbApiClient with the correct API version
        fb_client = FbApiClient(config_loader.credentials, api_version="21.0")

        # Initialize FbCommentManager
        comment_manager = FbCommentManager(fb_client)

        # Example post ID (replace with an actual post ID from your Facebook page)
        post_id = "122122055282142170"

        # 1. Post a new comment
        new_comment = comment_manager.post_comment(post_id, "interesting")
        if new_comment:
            logger.info(
                f"New comment posted successfully. Comment ID: {new_comment.get('id')}"
            )
            parent_comment_id = new_comment.get("id")
        else:
            logger.error("Failed to post new comment. Exiting.")
            return

        # Wait a bit to ensure the comment is processed
        time.sleep(8)

        # 2. Post replies to the new comment
        reply1 = comment_manager.post_comment(
            parent_comment_id, "and it seems it foes on during 2024 !!!!!"
        )
        logger.info(f"Replied to comment {parent_comment_id}: {reply1.get('message')}")
        time.sleep(6)
        reply2 = comment_manager.post_comment(
            parent_comment_id, "what do you all think?"
        )
        logger.info(f"Replied to comment {parent_comment_id}: {reply2.get('message')}")
        time.sleep(9)

        # 3. Add reactions to the parent comment
        comment_manager.react_to_comment(parent_comment_id, like=True)
        # Note: The current API doesn't allow adding non-LIKE reactions programmatically
        # We'll simulate other reactions for demonstration purposes
        time.sleep(4)

        # ----------- 4 mved below for when the post is not mine ------------

        time.sleep(5)
        # 5. Get replies to the parent comment
        replies = comment_manager.get_comment_replies(parent_comment_id)
        logger.info(f"\nReplies to the parent comment (ID: {parent_comment_id}):")
        for reply in replies:
            logger.info(
                f"- {reply.get('from', {}).get('name')}: {reply.get('message')}"
            )

        time.sleep(5)

        # 6. Get reactions for the parent comment
        reactions = comment_manager.get_comment_reactions(parent_comment_id)
        logger.info(f"\nReactions to the parent comment (ID: {parent_comment_id}):")
        for reaction_type, count in reactions.items():
            logger.info(f"- {reaction_type.capitalize()}: {count}")

        time.sleep(5)

        # 7. Like and reply to the last reply
        if replies:
            last_reply = replies[-1]
            last_reply_id = last_reply["id"]

            # Like the reply
            like_response = comment_manager.react_to_comment(last_reply_id, like=True)
            if like_response:
                logger.info(f"\nLiked reply: {last_reply_id}")
            else:
                logger.error(f"\nFailed to like reply: {last_reply_id}")

            # Reply to the reply
            reply_message = "Thank you for your reply! This is an automated response."
            reply_response = comment_manager.react_to_comment(
                last_reply_id, message=reply_message
            )
            if reply_response:
                logger.info(f"Replied to comment {last_reply_id}: {reply_message}")
            else:
                logger.error(f"Failed to reply to comment: {last_reply_id}")
        else:
            logger.info("\nNo replies found to like or respond to.")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)

        # 4. Retrieve comments for the post
    comments = comment_manager.get_post_comments(post_id, limit=10)
    logger.info(f"Retrieved {len(comments)} comments:")
    for comment in comments:
        logger.info(
            f"- {comment.get('from', {}).get('name')}: {comment.get('message')}"
        )


if __name__ == "__main__":
    main()
