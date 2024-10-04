"""A module for scraping Facebook pages using the facebook-scraper library."""

from typing import List, Dict, Any, Optional
from facebook_scraper import get_posts, get_profile


class FbScraper:
    """A class for scraping Facebook pages using the facebook-scraper library.

    This class provides methods to retrieve recent posts from a Facebook page
    without requiring API access.

    Attributes:
        None
    """

    @staticmethod
    def get_latest_posts(page_id: str, num_posts: int = 4) -> List[Dict[str, Any]]:
        """Retrieves the latest posts from a Facebook Page using web scraping.

        Args:
            page_id (str): The ID or username of the Facebook Page.
            num_posts (int, optional): The number of posts to retrieve (default: 4).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a post
                with the following keys: 'post_id', 'post_date', 'post_url', 'reactions',
                'comments', 'shares'. Returns an empty list if an error occurs.
        """
        try:
            posts = []
            for post in get_posts(page_id, pages=num_posts):
                post_data = {
                    "post_id": post.get("post_id"),
                    "post_date": post.get("time"),
                    "post_url": post.get("post_url"),
                    "reactions": post.get("likes"),
                    "comments": post.get("comments"),
                    "shares": post.get("shares"),
                }
                posts.append(post_data)

            return posts[
                :num_posts
            ]  # Ensure we only return the requested number of posts
        except Exception as e:
            print(f"Error scraping posts from page {page_id}: {e}")
            return []

    @staticmethod
    def format_post_data(posts: List[Dict[str, Any]]) -> str:
        """Formats the scraped post data into a readable string.

        Args:
            posts (List[Dict[str, Any]]): The list of post dictionaries returned by get_latest_posts.

        Returns:
            str: A formatted string containing the post information.
        """
        formatted_output = ""
        for post in posts:
            formatted_output += f"Post ID: {post['post_id']}\n"
            formatted_output += f"Date Posted: {post['post_date']}\n"
            formatted_output += f"Post URL: {post['post_url']}\n"
            formatted_output += f"Reactions: {post['reactions']}\n"
            formatted_output += f"Comments: {post['comments']}\n"
            formatted_output += f"Shares: {post['shares']}\n"
            formatted_output += "-" * 40 + "\n"
        return formatted_output

    @staticmethod
    def get_user_id(username: str) -> Optional[str]:
        """Attempts to retrieve the user ID for a given public Facebook username.

        Args:
            username (str): The Facebook username to look up.

        Returns:
            Optional[str]: The user ID if found, None otherwise.
        """
        try:
            profile = get_profile(username)
            return profile.get("id")
        except Exception as e:
            print(f"Error retrieving user ID for {username}: {e}")
            return None

    @staticmethod
    def get_page_id(page_name: str) -> Optional[str]:
        """Attempts to retrieve the page ID for a given Facebook page name.

        Args:
            page_name (str): The Facebook page name to look up.

        Returns:
            Optional[str]: The page ID if found, None otherwise.
        """
        try:
            # Fetch the first post from the page
            posts = list(get_posts(page_name, pages=1))
            if posts:
                # The page ID is typically part of the post ID
                post_id = posts[0].get("post_id")
                if post_id:
                    # Page ID is usually the part before the underscore
                    return post_id.split("_")[0]
            return None
        except Exception as e:
            print(f"Error retrieving page ID for {page_name}: {e}")
            return None

    @staticmethod
    def get_group_id(group_name: str) -> Optional[str]:
        """Attempts to retrieve the group ID for a given Facebook group name.

        Args:
            group_name (str): The Facebook group name or URL to look up.

        Returns:
            Optional[str]: The group ID if found, None otherwise.
        """
        try:
            # If a full URL is provided, extract the group name
            if "facebook.com/groups/" in group_name:
                group_name = group_name.split("facebook.com/groups/")[-1].split("/")[0]

            # Fetch the first post from the group
            posts = list(get_posts(group=group_name, pages=1))
            if posts:
                # The group ID is typically part of the post URL
                post_url = posts[0].get("post_url")
                if post_url:
                    # Try to extract the group ID from the URL
                    match = re.search(r"facebook\.com/groups/(\d+)", post_url)
                    if match:
                        return match.group(1)
            return None
        except Exception as e:
            print(f"Error retrieving group ID for {group_name}: {e}")
            return None
