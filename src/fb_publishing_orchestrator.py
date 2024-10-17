from typing import Dict, Any
from fb_post_tracker import FbPostTracker
from fb_post_manager import FbPostManager

class FbPublishingOrchestrator:
    def __init__(self, post_tracker: FbPostTracker, post_manager: FbPostManager, page_id: str):
        self.post_tracker = post_tracker
        self.post_manager = post_manager
        self.page_id = page_id

    def publish_next_post(self) -> None:
        post_data = self.post_tracker.get_next_post()
        if post_data:
            try:
                result = self.post_manager.publish_post(self.page_id, post_data)
                if result:
                    status = "Y"
                    post_id = result.get('id', '')
                    media_ids = self.post_tracker.get_media_ids(result)
                    self.post_tracker.update_post_status(post_data['row_index'], status, post_id, media_ids)
                    print(f"Post published successfully. Post ID: {post_id}")
                else:
                    self.post_tracker.update_post_status(post_data['row_index'], "Error")
                    print("Failed to publish post.")
            except Exception as e:
                print(f"Error publishing post: {str(e)}")
                self.post_tracker.update_post_status(post_data['row_index'], "Error")
        else:
            print("No posts to publish")

    # ... (rest of the code remains the same)
