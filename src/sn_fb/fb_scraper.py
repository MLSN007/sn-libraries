"""A module for scraping Facebook pages using Selenium."""

from typing import List, Dict, Any, Optional
import time
import re
import logging
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.keys import Keys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FbScraper:
    """A class for scraping Facebook pages using Selenium."""

    def __init__(self):
        """Initialize the FbScraper with a Selenium WebDriver."""
        try:
            # Specify the path to your ChromeDriver executable
            chrome_driver_path = r"C:\Users\manue\chrome-win64\chromedriver.exe"

            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--proxy-server='direct://'")
            chrome_options.add_argument("--proxy-bypass-list=*")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"]
            )
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
            )

            # Create a Service object
            service = Service(chrome_driver_path)

            # Initialize the Chrome WebDriver with the Service object and options
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except WebDriverException as e:
            raise Exception(f"Failed to initialize WebDriver: {e}")

    def __del__(self):
        """Close the browser when the FbScraper instance is destroyed."""
        if hasattr(self, "driver"):
            self.driver.quit()

    def get_latest_posts(
        self, entity_type: str, entity_id: str, num_posts: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the latest posts from a Facebook entity (user, page, or group) using Selenium.

        Args:
            entity_type (str): The type of entity ('user', 'page', or 'group').
            entity_id (str): The ID of the Facebook entity.
            num_posts (int, optional): The number of posts to retrieve (default: 4).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a post.
        """
        if entity_type not in ["user", "page", "group"]:
            raise ValueError(f"Invalid entity type: {entity_type}")

        url = f"https://m.facebook.com/{entity_id}"  # Use mobile version
        logger.info(f"Attempting to scrape posts from: {url}")
        self.driver.get(url)

        posts = []
        scroll_attempts = 0
        max_scroll_attempts = 10

        while len(posts) < num_posts and scroll_attempts < max_scroll_attempts:
            logger.info(f"Scrolling attempt {scroll_attempts + 1}/{max_scroll_attempts}")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # Wait longer for content to load

            try:
                # Wait for posts to be present
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for posts to load")

            # Find all post elements
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, "article")
            logger.info(f"Found {len(post_elements)} post elements")

            for post in post_elements[len(posts):num_posts]:
                try:
                    post_data = self._extract_post_data(post)
                    if post_data:
                        posts.append(post_data)
                        logger.info(f"Extracted post data: {post_data}")
                    else:
                        logger.warning("Failed to extract post data")
                except Exception as e:
                    logger.error(f"Error extracting post data: {e}", exc_info=True)

            scroll_attempts += 1

        logger.info(f"Total posts scraped: {len(posts)}")
        return posts

    def _extract_post_data(self, post_element) -> Dict[str, Any]:
        """
        Extracts data from a single post element.

        Args:
            post_element: The WebElement representing a post.

        Returns:
            Dict[str, Any]: A dictionary containing the post data.
        """
        post_data = {}

        try:
            # Extract post ID (this might need adjustment)
            post_id = post_element.get_attribute("id")
            post_data["post_id"] = post_id
            logger.info(f"Extracted post ID: {post_id}")

            # Extract post message
            message_elements = post_element.find_elements(By.CSS_SELECTOR, "div[data-sigil='m-feed-voice-subtitle']")
            if message_elements:
                post_data["message"] = message_elements[0].text
                logger.info(f"Extracted message: {post_data['message'][:50]}...")

            # Extract number of reactions (likes, etc.)
            reaction_elements = post_element.find_elements(By.CSS_SELECTOR, "div[data-sigil='reactions-sentence-container']")
            if reaction_elements:
                post_data["num_reactions"] = self._extract_number(reaction_elements[0].text)
                logger.info(f"Extracted number of reactions: {post_data['num_reactions']}")

            # Extract number of comments
            comment_elements = post_element.find_elements(By.CSS_SELECTOR, "div[data-sigil='m-feed-voice-subtitle'] a")
            if comment_elements:
                for element in comment_elements:
                    if "comment" in element.text.lower():
                        post_data["num_comments"] = self._extract_number(element.text)
                        logger.info(f"Extracted number of comments: {post_data['num_comments']}")
                        break

            # Extract media (if any)
            media_elements = post_element.find_elements(By.CSS_SELECTOR, "img[data-sigil='photo-image'], video")
            post_data["media"] = [elem.get_attribute("src") for elem in media_elements]
            logger.info(f"Extracted media: {len(post_data['media'])} items")

            # Extract link to the post
            link_elements = post_element.find_elements(By.CSS_SELECTOR, "a[href*='/story.php?']")
            if link_elements:
                post_data["link"] = link_elements[0].get_attribute("href")
                logger.info(f"Extracted post link: {post_data['link']}")

        except NoSuchElementException as e:
            logger.warning(f"Could not find element while extracting post data: {e}")
        except Exception as e:
            logger.error(f"Error extracting post data: {e}", exc_info=True)

        return post_data

    @staticmethod
    def _extract_number(text: str) -> int:
        """
        Extracts a number from a string.

        Args:
            text (str): The string containing a number.

        Returns:
            int: The extracted number, or 0 if no number is found.
        """
        match = re.search(r"\d+", text)
        return int(match.group()) if match else 0

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
        if entity_type == "user":
            return self.get_user_id(entity_name)
        elif entity_type == "page":
            return self.get_page_id(entity_name)
        elif entity_type == "group":
            return self.get_group_id(entity_name)
        else:
            raise ValueError(f"Invalid entity type: {entity_type}")

    def _scrape_id(
        self, url: str, id_pattern: str, alternative_method: callable
    ) -> Optional[str]:
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
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

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
                entity_id = self.driver.find_element(
                    By.XPATH, "//meta[@property='al:android:url']"
                )
                match = re.search(
                    r"fb://profile/(\d+)", entity_id.get_attribute("content")
                )
                return match.group(1) if match else None
            except NoSuchElementException:
                return None

        return self._scrape_id(
            f"https://www.facebook.com/{username}", r'"userID":"(\d+)"', alternative
        )

    def get_page_id(self, page_name: str) -> Optional[str]:
        """Attempts to retrieve the page ID for a given Facebook page name."""

        def alternative():
            try:
                entity_id = self.driver.find_element(
                    By.XPATH, "//meta[@property='al:android:url']"
                )
                content = entity_id.get_attribute("content")
                match = re.search(r"/(\d+)$", content)
                return match.group(1) if match else None
            except NoSuchElementException:
                return None

        return self._scrape_id(
            f"https://www.facebook.com/{page_name}", r'"pageID":"(\d+)"', alternative
        )

    def get_group_id(self, group_name: str) -> Optional[str]:
        """Attempts to retrieve the group ID for a given Facebook group name."""

        def scroll_and_wait():
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(random.uniform(1, 3))

        try:
            group_url = (
                group_name
                if "facebook.com/groups/" in group_name
                else f"https://www.facebook.com/groups/{group_name}"
            )
            self.driver.get(group_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Scroll a few times to load more content
            for _ in range(3):
                scroll_and_wait()

            # Try to find the group ID in various ways
            page_source = self.driver.page_source
            url = self.driver.current_url

            # Method 1: Look for groupID in page source
            match = re.search(r'"groupID":"(\d+)"', page_source)
            if match:
                return match.group(1)

            # Method 2: Look for group ID in URL
            match = re.search(r"facebook\.com/groups/(\d+)", url)
            if match:
                return match.group(1)

            # Method 3: Look for data-testid attribute
            try:
                group_element = self.driver.find_element(
                    By.CSS_SELECTOR, '[data-testid="group_sidebar"]'
                )
                group_id = group_element.get_attribute("data-id")
                if group_id:
                    return group_id
            except NoSuchElementException:
                pass

            # Method 4: Look for group name in title and extract nearby numbers
            title = self.driver.title
            match = re.search(rf"{re.escape(group_name)}.*?(\d+)", title, re.IGNORECASE)
            if match:
                return match.group(1)

            logger.warning(f"Could not find group ID for {group_name}")
            return None

        except TimeoutException:
            logger.error(f"Timeout while loading {group_url}")
        except WebDriverException as e:
            logger.error(f"WebDriver error while scraping {group_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return None