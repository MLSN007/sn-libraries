import sys
import os
from typing import Dict, Optional, Any, List
from pprint import pprint

# Get the absolute path of the current file
# current_file_path = os.path.abspath(__file__)
# print("current_file_path:", current_file_path)

# Get the directory of the current file
# current_dir = os.path.dirname(current_file_path)
# print("current_dir:", current_dir)


# Go up two levels to reach the root directory
# root_dir = os.path.abspath(os.path.join(current_dir, '..'))
# print("root_dir:", root_dir)

# Add the root directory to sys.path
# sys.path.append(root_dir)

# Construct the path to the 'src' directory
# # src_dir = os.path.join(root_dir, 'src')
# print("src_dir:", src_dir)

# Add the 'src' directory to sys.path
# sys.path.append(src_dir)

# print(sys.path)


from fb_api_client import FbApiClient
from fb_post_manager import FbPostManager
from fb_utils import FbUtils
from fb_comment_manager import FbCommentManager

print(FbApiClient)
print(FbPostManager)
print(FbUtils)
print(FbCommentManager)

