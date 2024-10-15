from typing import Dict, Any
from fb_post_tracker import FbPostTracker
from fb_post_manager import FbPostManager

class FbPublishingOrchestrator:
    def __init__(self, post_tracker: FbPostTracker, post_manager: FbPostManager):
        self.post_tracker = post_tracker
        self.post_manager = post_manager

    # ... (rest of the code remains the same)
