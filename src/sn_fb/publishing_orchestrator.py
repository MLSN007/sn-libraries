from typing import Dict, Any
from fb_post_tracker import FbPostTracker
from fb_post_manager import FbPostManager

class PublishingOrchestrator:
    def __init__(self, post_tracker: FbPostTracker, post_manager: FbPostManager):
        self.post_tracker = post_tracker
        self.post_manager = post_manager

    def publish_next_post(self) -> None:
        post_data = self.post_tracker.get_next_unpublished_post()
        if not post_data:
            print("No posts to publish")
            return

        print(f"Post data retrieved: {post_data}")

        try:
            post_result = self.post_manager.publish_post(post_data["page_id"], post_data)
            if post_result:
                print(f"Successfully published post with ID: {post_result.get('id') or post_result.get('post_id')}")
                print("Updating spreadsheet with published information")
                self.post_tracker.mark_post_as_published(post_data["row_index"], post_result)
                print("Finished updating spreadsheet")
            else:
                print("Failed to publish post")
                print("Updating spreadsheet with failure status")
                self.post_tracker.update_post_status(post_data["row_index"], "Failed")
        except Exception as e:
            print(f"Error publishing post: {str(e)}")
            print("Updating spreadsheet with error status")
            self.post_tracker.update_post_status(post_data["row_index"], "Error")
