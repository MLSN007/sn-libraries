"""
Module for managing all proxy-related operations including configuration, connection, and rotation.
"""

import time
import random
import logging
from pathlib import Path
from typing import Dict, Optional, List, Set
import requests
from collections import deque
import os
from dotenv import load_dotenv
import json

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ProxyManager:
    """Manages all proxy-related operations."""

    def __init__(self, config: Optional[Dict] = None, max_retries: int = 3) -> None:
        """
        Initialize the proxy manager with configuration.

        Args:
            config (Optional[Dict]): Configuration dictionary for proxy settings.
            max_retries (int): Maximum number of retries for proxy rotation.
        """
        load_dotenv()  # Load environment variables

        # Initialize proxy credentials with all required fields
        self.proxy_credentials: Dict[str, Optional[str]] = {
            "host": os.getenv("PROXY_HOST", "geo.iproyal.com"),
            "port": os.getenv("PROXY_PORT", "12321"),
            "username": os.getenv("PROXY_USERNAME"),
            "password": os.getenv("PROXY_PASSWORD"),
            "base_sessions": [],  # Initialize as empty list by default
            "country_code": os.getenv("PROXY_COUNTRY_CODE", "ES"),
            "city": os.getenv("PROXY_CITY", "madrid"),
            "lifetime": os.getenv("PROXY_LIFETIME", "60m"),
            "streaming": os.getenv("PROXY_STREAMING", "1")
        }

        # Validate required credentials
        if not self.proxy_credentials["username"] or not self.proxy_credentials["password"]:
            logger.error("Proxy credentials not found in environment variables.")
            raise ValueError("Proxy credentials not found in environment variables")

        # Initialize other attributes
        self.proxy_file_path: Path = Path(__file__).parent.parent / "proxy_list.txt"
        self.last_rotation_time: float = time.time()
        self.rotation_interval: int = 25 * 60  # 25 minutes
        self.proxy_list: List[str] = []
        self.used_ips: Set[str] = set()
        self.available_proxies: deque = deque()
        self.max_retries: int = max_retries

        # Initialize proxy connection
        self.current_proxy: Optional[str] = None
        self.current_proxies: Optional[Dict[str, str]] = None

        # Initialize pool and first proxy
        self._initialize_proxy_pool()
        if not self._load_and_set_proxy():
            logger.error("Failed to initialize first proxy connection.")
            raise ValueError("Failed to initialize first proxy connection.")

    def _initialize_proxy_pool(self) -> None:
        """Initialize the pool of available proxies."""
        logger.info("Initializing proxy pool")
        
        try:
            # Read proxies from file
            if self.proxy_file_path.exists():
                with open(self.proxy_file_path, 'r') as f:
                    self.proxy_list = [line.strip() for line in f if line.strip()]
            else:
                logger.warning("Proxy list file not found at: %s", self.proxy_file_path)
                self.proxy_list = []
                
            if not self.proxy_list:
                logger.error("No proxies available in proxy list")
                raise ValueError("No proxies available")
                
            # Initialize the deque with all available proxies
            self.available_proxies = deque(self.proxy_list)
            logger.info("Initialized proxy pool with %d proxies", len(self.available_proxies))
            
        except Exception as e:
            logger.error("Failed to initialize proxy pool: %s", e)
            raise

    def _load_and_set_proxy(self) -> bool:
        """
        Load and set a new proxy, ensuring a unique IP.

        Returns:
            bool: True if a unique proxy was set successfully, False otherwise.
        """
        max_attempts: int = self.max_retries
        attempts: int = 0

        while attempts < max_attempts:
            attempts += 1

            # If we've tried all available proxies, refresh the pool
            if not self.available_proxies:
                logger.info("Refreshing proxy pool...")
                self.clear_ip_history()  # Reset used IPs
                self.available_proxies.extend(self.proxy_list)
                random.shuffle(self.proxy_list)

            try:
                proxy_string: str = self.available_proxies.popleft()
                parts: List[str] = proxy_string.split(":")
                if len(parts) < 4:
                    logger.warning("Invalid proxy format: %s", proxy_string)
                    continue

                host, port, username, password_and_params = parts[0], parts[1], parts[2], ":".join(parts[3:])

                # Format proxy strings
                self.current_proxy = f"{username}:{password_and_params}@{host}:{port}"
                self.current_proxies = {
                    "http": f"http://{self.current_proxy}",
                    "https": f"http://{self.current_proxy}",
                }

                # Verify IP
                response = requests.get(
                    "http://ip-api.com/json",
                    proxies=self.current_proxies,
                    timeout=30
                )
                data = response.json()
                current_ip: Optional[str] = data.get("query")

                if current_ip and current_ip not in self.used_ips:
                    self.used_ips.add(current_ip)
                    self.last_rotation_time = time.time()
                    logger.info("Set new unique proxy IP: %s", current_ip)
                    logger.info("Location: %s, %s", data.get("city", "Unknown"), data.get("country", "Unknown"))
                    return True

                logger.warning("Duplicate IP %s detected, trying next proxy...", current_ip)
                time.sleep(1)  # Small delay before next attempt

            except Exception as e:
                logger.error("Error with proxy attempt %d: %s", attempts, e)
                time.sleep(1)
                continue

        logger.error("Failed to find a unique proxy after %d attempts.", max_attempts)
        return False

    def load_proxy_list(self) -> List[str]:
        """
        Load proxy strings from the proxy list file.

        Returns:
            List[str]: A list of proxy strings.
        """
        proxy_file_path: Path = Path(__file__).parent.parent / "proxy_list.txt"

        try:
            with proxy_file_path.open("r") as f:
                proxies: List[str] = [line.strip() for line in f if line.strip()]
                logger.info("Loaded %d proxies from %s", len(proxies), proxy_file_path)
                return proxies
        except FileNotFoundError:
            logger.warning("Proxy list file not found at %s", proxy_file_path)
            return self.get_fresh_proxy_list()

    def get_current_proxy(self) -> Optional[str]:
        """
        Get the current proxy string.

        Returns:
            Optional[str]: The current proxy string if set, else None.
        """
        return self.current_proxy

    def get_current_proxies(self) -> Dict[str, str]:
        """
        Get the current proxy configuration in requests format.
        
        Returns:
            Dict[str, str]: Dictionary with 'http' and 'https' proxy configurations
        """
        if not self.current_proxy:
            raise ValueError("No proxy currently set")
        
        return {
            'http': f'http://{self.current_proxy}',    # Change from socks5:// to http://
            'https': f'http://{self.current_proxy}'    # Change from socks5:// to http://
        }

    def should_rotate(self) -> bool:
        """
        Check if the proxy should be rotated based on the rotation interval.

        Returns:
            bool: True if rotation is needed, False otherwise.
        """
        return (time.time() - self.last_rotation_time) >= self.rotation_interval

    def rotate_if_needed(self) -> bool:
        """
        Rotate the proxy if the rotation interval has passed.

        Returns:
            bool: True if rotation was successful or not needed, False otherwise.
        """
        if self.should_rotate():
            logger.info("Rotating proxy...")
            return self._load_and_set_proxy()
        return True

    def validate_connection(self) -> bool:
        """
        Validate the current proxy connection.
        
        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            proxies = self.get_current_proxies()
            
            # Explicitly configure for HTTP/HTTPS
            session = requests.Session()
            response = session.get(
                'http://ip-api.com/json',
                proxies=proxies,
                timeout=30,
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Connected via IP: %s in %s, %s", 
                           data.get('query'), 
                           data.get('city'), 
                           data.get('country'))
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error validating connection: %s", e)
            return False

    def get_fresh_proxy_list(self, sessions: Optional[List[str]] = None) -> List[str]:
        """
        Generate a fresh proxy list based on current configuration.

        Args:
            sessions (Optional[List[str]]): List of session identifiers.

        Returns:
            List[str]: A list of formatted proxy strings.
        """
        if not sessions:
            if not self.proxy_credentials["base_sessions"]:
                logger.error("No proxy sessions configured.")
                raise ValueError("No proxy sessions configured.")

            base_sessions = self.proxy_credentials["base_sessions"]
            sessions = [f"{session.strip()}_{i}" for session in base_sessions for i in range(5)]

        proxy_strings: List[str] = [
            f"{self.proxy_credentials['host']}:{self.proxy_credentials['port']}"
            f":{self.proxy_credentials['username']}:{self.proxy_credentials['password']}"
            f"_country-{self.config['country_code'].lower()}"
            f"_city-{self.config['city']}"
            f"_session-{session}"
            f"_lifetime-{self.config['lifetime']}"
            f"_streaming-{self.config['streaming']}"
            for session in sessions
        ]

        logger.info("Generated fresh proxy list with %d proxies.", len(proxy_strings))
        return proxy_strings

    def clear_ip_history(self) -> None:
        """
        Clear the history of used IPs.
        """
        self.used_ips.clear()
        logger.info("Cleared IP history.")

    def _format_proxy_string(self, session_id: str = "") -> str:
        """
        Format proxy string with credentials and session.
        
        Args:
            session_id (str): Optional session identifier
            
        Returns:
            str: Formatted proxy string for HTTP/HTTPS proxy
        """
        # Your proxy format is:
        # host:port:username:password_country-es_city-madrid_session-xxx_lifetime-1h_streaming-1
        
        credentials = self.proxy_credentials
        proxy_string = (
            f"{credentials['username']}:{credentials['password']}"
            f"@{credentials['host']}:{credentials['port']}"
        )
        return proxy_string

    def _load_proxy_list(self) -> List[str]:
        """
        Load proxy list from file.
        
        Returns:
            List[str]: List of proxy strings
        """
        try:
            with open(self.proxy_file_path, 'r') as f:
                # Each line should be in format:
                # geo.iproyal.com:12321:username:password_country-es_city-madrid_session-xxx_lifetime-1h_streaming-1
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error("Proxy list file not found at: %s", self.proxy_file_path)
            return []

    def _format_proxy_string(self, proxy_line: str) -> str:
        """
        Format proxy string from proxy list format to requests format.
        
        Args:
            proxy_line (str): Raw proxy string from proxy_list.txt
            
        Returns:
            str: Formatted proxy string for HTTP/HTTPS proxy
        """
        try:
            # Split the proxy line into components
            host, port, username, password_with_config = proxy_line.split(':')
            # Format into standard proxy URL format
            return f"{username}:{password_with_config}@{host}:{port}"
        except ValueError as e:
            logger.error("Invalid proxy format in line: %s", proxy_line)
            raise ValueError(f"Invalid proxy format: {e}")

    def get_current_proxies(self) -> Dict[str, str]:
        """
        Get the current proxy configuration in requests format.
        
        Returns:
            Dict[str, str]: Dictionary with HTTP/HTTPS proxy configurations
        """
        if not self.current_proxy:
            raise ValueError("No proxy currently set")
        
        # Explicitly format as HTTP proxy
        proxy_url = f"http://{self.current_proxy}"
        return {
            'http': proxy_url,
            'https': proxy_url
        }
