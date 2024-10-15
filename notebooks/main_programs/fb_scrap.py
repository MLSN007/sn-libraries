"""A script to demonstrate Facebook scraping capabilities."""

from typing import Optional
from fb_scraper import FbScraper

def main():
    """Main function to demonstrate Facebook scraping."""
    # Hardcoded variables for demonstration
    user_name = "JohnKlanick"  # Mark Zuckerberg's profile
    page_name = "JKTravelingAroundTheWorld"  # Facebook's official page
    group_name = "travelcrazyaroundtheworld"  # A public group about metaverse

    # Initialize the FbScraper
    scraper = FbScraper()

    try:
        # Scrape user ID
        user_id = scraper.get_entity_id('user', user_name)
        print(f"User '{user_name}' ID: {user_id}")

        # Scrape page ID
        page_id = scraper.get_entity_id('page', page_name)
        print(f"Page '{page_name}' ID: {page_id}")

        # Scrape group ID
        group_id = scraper.get_entity_id('group', group_name)
        print(f"Group '{group_name}' ID: {group_id}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Ensure the browser is closed even if an exception occurs
        del scraper

if __name__ == "__main__":
    main()
