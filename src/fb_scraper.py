"""A module for scraping Facebook pages using Selenium."""

from typing import List, Dict, Any, Optional
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

class FbScraper:
    """A class for scraping Facebook pages using Selenium."""

    def __init__(self):
        """Initialize the FbScraper with a Selenium WebDriver."""
        try:
            # Specify the path to your ChromeDriver executable
            chrome_driver_path = r"C:\Users\manue\chrome-win64\chromedriver.exe"
            
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode (optional)
            
            # Create a Service object
            service = Service(chrome_driver_path)
            
            # Initialize the Chrome WebDriver with the Service object and options
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
        except WebDriverException as e:
            raise Exception(f"Failed to initialize WebDriver: {e}")

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

    def get_entity_id(self, entity_type: str, entity_name: str) -> Optional[str]:
        """
        Scrape a Facebook entity (user, page, or group) and return its ID.

        Args:
            entity_type (str): The type of entity to scrape ('user', 'page', or 'group').
            entity_name (str): The name or username of the entity to scrape.

        Returns:
            Optional[str]: The ID of the entity if found, None otherwise.

        Raises:
            ValueError: If an invalid entity type is provided.
        """
        if entity_type == 'user':
            return self.get_user_id(entity_name)
        elif entity_type == 'page':
            return self.get_page_id(entity_name)
        elif entity_type == 'group':
            return self.get_group_id(entity_name)
        else:
            raise ValueError(f"Invalid entity type: {entity_type}")

    def _scrape_id(self, url: str, id_pattern: str, alternative_method: callable) -> Optional[str]:
        """
        Helper method to scrape entity IDs.

        Args:
            url (str): The URL to scrape.
            id_pattern (str): The regex pattern to search for the ID.
            alternative_method (callable): A function to call if the primary method fails.

        Returns:
            Optional[str]: The scraped ID if found, None otherwise.
        """
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            page_source = self.driver.page_source
            match = re.search(id_pattern, page_source)
            if match:
                return match.group(1)

            return alternative_method()
        except TimeoutException:
            print(f"Timeout while loading {url}")
        except NoSuchElementException:
            print(f"Required element not found on {url}")
        except WebDriverException as e:
            print(f"WebDriver error while scraping {url}: {e}")
        return None

    def get_user_id(self, username: str) -> Optional[str]:
        """Attempts to retrieve the user ID for a given public Facebook username."""
        def alternative():
            try:
                entity_id = self.driver.find_element(By.XPATH, "//meta[@property='al:android:url']")
                match = re.search(r'fb://profile/(\d+)', entity_id.get_attribute('content'))
                return match.group(1) if match else None
            except NoSuchElementException:
                return None

        return self._scrape_id(f"https://www.facebook.com/{username}", r'"userID":"(\d+)"', alternative)

    def get_page_id(self, page_name: str) -> Optional[str]:
        """Attempts to retrieve the page ID for a given Facebook page name."""
        def alternative():
            try:
                entity_id = self.driver.find_element(By.XPATH, "//meta[@property='al:android:url']")
                content = entity_id.get_attribute('content')
                match = re.search(r'/(\d+)$', content)
                return match.group(1) if match else None
            except NoSuchElementException:
                return None

        return self._scrape_id(f"https://www.facebook.com/{page_name}", r'"pageID":"(\d+)"', alternative)

    def get_group_id(self, group_name: str) -> Optional[str]:
        """Attempts to retrieve the group ID for a given Facebook group name."""
        def alternative():
            current_url = self.driver.current_url
            match = re.search(r'facebook\.com/groups/(\d+)', current_url)
            return match.group(1) if match else None

        group_url = group_name if "facebook.com/groups/" in group_name else f"https://www.facebook.com/groups/{group_name}"
        return self._scrape_id(group_url, r'"groupID":"(\d+)"', alternative)
