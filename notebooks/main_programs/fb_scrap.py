"""A script to demonstrate Facebook scraping capabilities."""

from typing import Optional
from fb_scraper import FbScraper
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to demonstrate Facebook scraping."""
    # Hardcoded variables for demonstration
    user_name = "JohnKlanick"  # Example user profile
    page_name = "DisfrutandoHuelva"  # Example Facebook page
    # group_name = "BestDestinationsToTravel"  # Example public group (commented out)

    # Initialize the FbScraper
    scraper = FbScraper()

    try:
        logger.info("Starting Facebook scraping")

        # Scrape user ID
        user_id = scraper.get_entity_id('user', user_name)
        logger.info(f"User '{user_name}' ID: {user_id}")

        # Scrape page ID
        page_id = scraper.get_entity_id('page', page_name)
        logger.info(f"Page '{page_name}' ID: {page_id}")

        # Commented out group ID scraping
        # group_id = scraper.get_entity_id('group', group_name)
        # logger.info(f"Group '{group_name}' ID: {group_id}")
        # if group_id is None:
        #     logger.warning(f"Failed to retrieve group ID for '{group_name}'. Trying direct URL...")
        #     group_id = scraper.get_group_id(f"https://www.facebook.com/groups/{group_name}")
        #     logger.info(f"Group '{group_name}' ID (second attempt): {group_id}")

        # Scrape the 2 latest posts from the user
        if user_id:
            user_posts = scraper.get_latest_posts('user', user_id, num_posts=2)
            logger.info(f"\nLatest posts from user '{user_name}':")
            for i, post in enumerate(user_posts, 1):
                logger.info(f"\nPost {i}:")
                logger.info(f"Post ID: {post.get('post_id', 'N/A')}")
                logger.info(f"Message: {post.get('message', 'N/A')[:100]}..." if post.get('message') else "Message: N/A")
                logger.info(f"Comments: {post.get('num_comments', 'N/A')}")
                logger.info(f"Likes: {post.get('num_likes', 'N/A')}")
                logger.info(f"Media: {', '.join(post.get('media', [])) or 'N/A'}")
                logger.info(f"Link: {post.get('link', 'N/A')}")

        # Scrape the 2 latest posts from the page
        if page_id:
            page_posts = scraper.get_latest_posts('page', page_id, num_posts=2)
            logger.info(f"\nLatest posts from page '{page_name}':")
            for i, post in enumerate(page_posts, 1):
                logger.info(f"\nPost {i}:")
                logger.info(f"Post ID: {post.get('post_id', 'N/A')}")
                logger.info(f"Message: {post.get('message', 'N/A')[:100]}..." if post.get('message') else "Message: N/A")
                logger.info(f"Comments: {post.get('num_comments', 'N/A')}")
                logger.info(f"Likes: {post.get('num_likes', 'N/A')}")
                logger.info(f"Media: {', '.join(post.get('media', [])) or 'N/A'}")
                logger.info(f"Link: {post.get('link', 'N/A')}")

    except ValueError as e:
        logger.error(f"Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        logger.info("Finishing Facebook scraping")
        # Ensure the browser is closed even if an exception occurs
        del scraper

if __name__ == "__main__":
    main()
