"""A module for scraping Facebook pages using Selenium."""

from typing import List, Dict, Any, Optional
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class FbScraper:
    """A class for scraping Facebook pages using Selenium.

    This class provides methods to retrieve recent posts from a Facebook page
    and extract user, page, and group IDs.

    Attributes:
        driver: The Selenium WebDriver instance.
    """

    def __init__(self):
        """Initialize the FbScraper with a Selenium WebDriver."""
        # Specify the path to your ChromeDriver executable
        chrome_driver_path = r"C:\Users\manue\chrome-win64\chromedriver.exe"
        
        # Create a Service object
        service = Service(chrome_driver_path)
        
        # Initialize the Chrome WebDriver with the Service object
        self.driver = webdriver.Chrome(service=service)
        self.driver.implicitly_wait(10)  # Wait up to 10 seconds for elements to appear

    def __del__(self):
        """Close the browser when the FbScraper instance is destroyed."""
        if hasattr(self, 'driver'):
            self.driver.quit()

    @staticmethod
    def get_latest_posts(page_id: str, num_posts: int = 4) -> List[Dict[str, Any]]:
        """Retrieves the latest posts from a Facebook Page using web scraping.

        This method is left as a placeholder. Implement Selenium-based scraping
        for posts if needed.

        Args:
            page_id (str): The ID or username of the Facebook Page.
            num_posts (int, optional): The number of posts to retrieve (default: 4).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a post.
        """
        # Implement Selenium-based post scraping here if needed
        return []

    def get_user_id(self, username: str) -> Optional[str]:
        """Attempts to retrieve the user ID for a given public Facebook username.

        Args:
            username (str): The Facebook username to look up.

        Returns:
            Optional[str]: The user ID if found, None otherwise.
        """
        try:
            self.driver.get(f"https://www.facebook.com/{username}")
            time.sleep(2)  # Wait for any redirects or JavaScript to load

            # Look for the user ID in the page source
            page_source = self.driver.page_source
            match = re.search(r'"userID":"(\d+)"', page_source)
            if match:
                return match.group(1)

            # If not found, try an alternative method
            entity_id = self.driver.find_element(By.XPATH, "//meta[@property='al:android:url']")
            if entity_id:
                match = re.search(r'fb://profile/(\d+)', entity_id.get_attribute('content'))
                if match:
                    return match.group(1)

            return None
        except Exception as e:
            print(f"Error retrieving user ID for {username}: {e}")
            return None

    def get_page_id(self, page_name: str) -> Optional[str]:
        """Attempts to retrieve the page ID for a given Facebook page name.

        Args:
            page_name (str): The Facebook page name to look up.

        Returns:
            Optional[str]: The page ID if found, None otherwise.
        """
        try:
            self.driver.get(f"https://www.facebook.com/{page_name}")
            time.sleep(2)  # Wait for any redirects or JavaScript to load

            # Look for the page ID in the page source
            page_source = self.driver.page_source
            match = re.search(r'"pageID":"(\d+)"', page_source)
            if match:
                return match.group(1)

            # If not found, try an alternative method
            entity_id = self.driver.find_element(By.XPATH, "//meta[@property='al:android:url']")
            if entity_id:
                content = entity_id.get_attribute('content')
                match = re.search(r'/(\d+)$', content)
                if match:
                    page_id = match.group(1)
                else:
                    page_id = None
            except NoSuchElementException:
                page_id = None

            return page_id
        except Exception as e:
            print(f"Error retrieving page ID for {page_name}: {e}")
            return None

    def get_group_id(self, group_name: str) -> Optional[str]:
        """Attempts to retrieve the group ID for a given Facebook group name.

        Args:
            group_name (str): The Facebook group name or URL to look up.

        Returns:
            Optional[str]: The group ID if found, None otherwise.
        """
        try:
            if "facebook.com/groups/" in group_name:
                group_url = group_name
            else:
                group_url = f"https://www.facebook.com/groups/{group_name}"

            self.driver.get(group_url)
            time.sleep(2)  # Wait for any redirects or JavaScript to load

            # Look for the group ID in the page source
            page_source = self.driver.page_source
            match = re.search(r'"groupID":"(\d+)"', page_source)
            if match:
                return match.group(1)

            # If not found, try an alternative method
            current_url = self.driver.current_url
            match = re.search(r'facebook\.com/groups/(\d+)', current_url)
            if match:
                return match.group(1)

            return None
        except Exception as e:
            print(f"Error retrieving group ID for {group_name}: {e}")
            return None
