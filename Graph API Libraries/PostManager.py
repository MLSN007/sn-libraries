
import facebook

class PostManager:
    def __init__(self, api_client):
        self.api_client = api_client

    def publish_text_post(self, page_id, message):
        """Publishes a text-only post on the specified Facebook Page."""
        graph = self.api_client.get_graph_api_object()
        try:
            post = graph.put_object(
                parent_object=page_id,
                connection_name='feed',
                message=message
            )
            print(f"Post published successfully. Post ID: {post['id']}")
        except facebook.GraphAPIError as e:
            print(f"Error publishing post: {e.message}")

    def publish_photo_post(self, page_id, message, photo_path):
        """Publishes a post with a photo and text on the specified Facebook Page."""
        graph = self.api_client.get_graph_api_object()
        with open(photo_path, 'rb') as image_file:
            try:
                post = graph.put_photo(
                    parent_object=page_id,
                    connection_name='photos',
                    message=message,
                    image=image_file
                )
                print(f"Post with photo published successfully. Post ID: {post['post_id']}")
            except facebook.GraphAPIError as e:
                print(f"Error publishing post with photo: {e.message}")
                

    # ... (Other methods for publishing multi-photo and video posts will be added later)