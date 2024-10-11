from fb_post_tracker import FacebookPostTracker
from fb_post_manager import FacebookPostManager

def main():
    tracker = FacebookPostTracker(account_id="JK", spreadsheet_id="your_spreadsheet_id")
    fb_manager = FacebookPostManager()  # Initialize your Facebook Post Manager

    post_data = tracker.get_next_unpublished_post()
    if not post_data:
        print("No posts to publish")
        return

    post_type = post_data.get('Type', '').lower()
    post_id = None

    try:
        if post_type == 'text':
            post_id = fb_manager.publish_text_post(post_data)
        elif post_type == 'single photo':
            post_id = fb_manager.publish_single_photo_post(post_data)
        elif post_type == 'multiple photo':
            post_id = fb_manager.publish_multiple_photo_post(post_data)
        elif post_type == 'video':
            post_id = fb_manager.publish_video_post(post_data)
        elif post_type == 'reel':
            post_id = fb_manager.publish_reel_post(post_data)
        elif post_type == 'carousel':
            post_id = fb_manager.publish_carousel_post(post_data)
        else:
            print(f"Unknown post type: {post_type}")
            return

        if post_id:
            tracker.mark_post_as_published(post_data['row_index'], post_id)
            tracker.add_post_to_published_log(post_data)
            print(f"Successfully published {post_type} post with ID: {post_id}")
        else:
            print(f"Failed to publish {post_type} post")
            tracker.update_post_status(post_data['row_index'], "Failed")

    except Exception as e:
        print(f"Error publishing {post_type} post: {str(e)}")
        tracker.update_post_status(post_data['row_index'], "Error")

if __name__ == "__main__":
    main()