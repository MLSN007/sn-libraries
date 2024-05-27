import os
from typing import Dict, Optional, Any
import json
import facebook
from facebook_api_client import FacebookAPIClient
from post_manager import PostManager
from utils import Utils

# Load credentials (RELEVANT IF I AM GOING TO USE
# DIFFERENT CREDENTIALS THAT THOSE DEFINED ON THE FacebookAPIClient Class load credentials)

try:
    app_id = os.environ["FB_ES_App_id"]
    app_secret = os.environ["FB_ES_App_secret"]
    access_token = os.environ["FB_ES_ES_App_token"]
    page_id = os.environ["FB_ES_Pg_id"]
except KeyError:
    print("Error: Environment variables not set. Please set them before running the tests.")
    exit(1)  # Exit with error code


# Instantiate the FacebookAPIClient and PostManager
fb_client = FacebookAPIClient(app_id, app_secret, access_token, page_id)
post_manager = PostManager(fb_client)
utils = Utils(fb_client)