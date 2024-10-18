from typing import Dict, Any, Optional
from fb_post_tracker import FbPostTracker
from fb_post_manager import FbPostManager
import logging

logger = logging.getLogger(__name__)

class FbPublishingOrchestrator:
    def __init__(self, post_tracker: FbPostTracker, post_manager: FbPostManager, page_id: str):
        self.post_tracker = post_tracker
        self.post_manager = post_manager
        self.page_id = page_id

    def publish_next_post(self) -> Optional[Dict[str, Any]]:
        next_post = self.post_tracker.get_next_post()
        if not next_post:
            logger.info("No posts available to publish.")
            return None

        post_result = self.post_manager.publish_post(self.page_id, next_post)
        if post_result:
            self.post_tracker.mark_post_as_published(next_post['row_index'], post_result)
            self.post_tracker.add_post_to_published_log(next_post, post_result)
            logger.info(f"Post published and tracked successfully. Post ID: {post_result.get('id')}")
            return post_result
        else:
            logger.error("Failed to publish post.")
            return None

    # ... (rest of the code remains the same)
