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


class ProxyManager:
    """Manages all proxy-related operations."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize proxy manager with configuration."""
        load_dotenv()  # Load environment variables
        
        # Load proxy credentials
        self.proxy_credentials = {
            "host": os.getenv("PROXY_HOST", "geo.iproyal.com"),
            "port": os.getenv("PROXY_PORT", "32325"),
            "username": os.getenv("PROXY_USERNAME"),
            "password": os.getenv("PROXY_PASSWORD"),
            "base_sessions": os.getenv("PROXY_BASE_SESSIONS", "").split(",")
        }
        
        # Load location config from environment
        self.config = config or {
            "country_code": os.getenv("PROXY_COUNTRY_CODE", "ES"),
            "country_name": os.getenv("PROXY_COUNTRY_NAME", "Spain"),
            "city": os.getenv("PROXY_CITY", "huelva").lower(),
            "lifetime": os.getenv("PROXY_LIFETIME", "30m"),
            "streaming": os.getenv("PROXY_STREAMING", "1")
        }
        
        # Validate required credentials
        if not self.proxy_credentials["username"] or not self.proxy_credentials["password"]:
            raise ValueError("Proxy credentials not found in environment variables")
        
        # Initialize other attributes
        self.proxy_file_path = Path(__file__).parent.parent / "proxy_list.txt"
        self.last_rotation_time = time.time()
        self.rotation_interval = 25 * 60  # 25 minutes
        self.proxy_list = []
        self.used_ips: Set[str] = set()
        self.available_proxies = deque()
        self.max_retries = 3
        
        # Initialize proxy connection
        self.current_proxy = None
        self.current_proxies = None
        
        # Initialize pool and first proxy
        self._initialize_proxy_pool()
        if not self._load_and_set_proxy():
            raise ValueError("Failed to initialize first proxy connection")

    def _initialize_proxy_pool(self) -> None:
        """Initialize the pool of available proxies."""
        # Use either file-based proxies OR generated proxies, not both
        if os.path.exists(self.proxy_file_path):
            logger.info("Using proxies from proxy_list.txt")
            self.proxy_list = self.load_proxy_list()
        else:
            logger.info("Generating proxy list from base sessions")
            if not self.proxy_credentials["base_sessions"]:
                raise ValueError("No proxy sessions configured in .env file")

            base_sessions = self.proxy_credentials["base_sessions"]
            extended_sessions = []

            for session in base_sessions:
                for i in range(5):
                    extended_sessions.append(f"{session.strip()}_{i}")

            self.proxy_list = self.get_fresh_proxy_list(extended_sessions)

        self.available_proxies.extend(self.proxy_list)
        logger.info(f"Initialized proxy pool with {len(self.proxy_list)} proxies")

    def _load_and_set_proxy(self) -> bool:
        """Load and set a new proxy, ensuring unique IP."""
        max_attempts = len(self.proxy_list)  # Try all possible proxies
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            # If we've tried all available proxies, refresh the pool
            if not self.available_proxies:
                logger.info("Refreshing proxy pool...")
                self.clear_ip_history()  # Reset used IPs
                self.available_proxies.extend(self.proxy_list)
                random.shuffle(list(self.available_proxies))

            try:
                proxy_string = self.available_proxies.popleft()
                parts = proxy_string.split(":")
                host, port, username, password_and_params = (
                    parts[0],
                    parts[1],
                    parts[2],
                    ":".join(parts[3:]),
                )

                # Format proxy strings
                self.current_proxy = (
                    f"socks5://{username}:{password_and_params}@{host}:{port}"
                )
                self.current_proxies = {
                    "http": self.current_proxy,
                    "https": self.current_proxy,
                }

                # Verify IP
                response = requests.get(
                    "http://ip-api.com/json", proxies=self.current_proxies, timeout=30
                )
                data = response.json()
                current_ip = data.get("query")

                if current_ip and current_ip not in self.used_ips:
                    self.used_ips.add(current_ip)
                    self.last_rotation_time = time.time()
                    logger.info(f"Set new unique proxy IP: {current_ip}")
                    logger.info(
                        f"Location: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
                    )
                    return True

                logger.warning(
                    f"Duplicate IP {current_ip} detected, trying next proxy..."
                )
                time.sleep(1)  # Small delay before next attempt

            except Exception as e:
                logger.error(f"Error with proxy attempt {attempts}: {e}")
                time.sleep(1)
                continue

        logger.error("Failed to find unique proxy after trying all options")
        return False

    def load_proxy_list(self) -> List[str]:
        """Load proxy strings from file."""
        project_root = Path(__file__).parent.parent
        proxy_file_path = project_root / "proxy_list.txt"

        try:
            with open(proxy_file_path, "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
                logger.info(f"Loaded {len(proxies)} proxies from {proxy_file_path}")
                return proxies
        except FileNotFoundError:
            logger.warning(f"Proxy list file not found at {proxy_file_path}")
            return self.get_fresh_proxy_list()

    def get_current_proxy(self) -> str:
        """Get current proxy string."""
        return self.current_proxy

    def get_current_proxies(self) -> Dict[str, str]:
        """Get current proxies dictionary."""
        return self.current_proxies

    def should_rotate(self) -> bool:
        """Check if proxy should be rotated."""
        return time.time() - self.last_rotation_time >= self.rotation_interval

    def rotate_if_needed(self) -> bool:
        """
        Rotate proxy if needed, ensuring unique IP.

        Returns:
            bool: True if rotation successful
        """
        if self.should_rotate():
            logger.info("Rotating proxy...")
            return self._load_and_set_proxy()
        return True

    def validate_connection(self) -> bool:
        """
        Validate current proxy connection and location.

        Returns:
            bool: True if connection is valid and in correct location
        """
        try:
            response = requests.get(
                "http://ip-api.com/json", proxies=self.current_proxies, timeout=30
            )

            data = response.json()
            logger.info("Location Details:")
            logger.info(f"  Country: {data.get('country', 'Unknown')}")
            logger.info(f"  City: {data.get('city', 'Unknown')}")
            logger.info(f"  ISP: {data.get('isp', 'Unknown')}")

            # Verify country code
            if data.get("countryCode") != self.config["country_code"]:
                logger.error(
                    f"❌ Wrong country: {data.get('country')} (Expected: {self.config['country_name']})"
                )
                return False

            # Verify city if specified
            if (
                self.config["city"]
                and data.get("city", "").lower() != self.config["city"]
            ):
                logger.warning(
                    f"⚠️ Different city: {data.get('city')} (Expected: {self.config['city']})"
                )
                # Don't fail on city mismatch, just warn

            logger.info("✅ Location verification passed")
            return True

        except Exception as e:
            logger.error(f"Failed to validate proxy: {e}")
            return False

    def get_fresh_proxy_list(self, sessions: Optional[List[str]] = None) -> List[str]:
        """Generate fresh proxy list with current configuration."""
        if not sessions:
            if not self.proxy_credentials["base_sessions"]:
                raise ValueError("No proxy sessions configured")
            base_sessions = self.proxy_credentials["base_sessions"]
            sessions = []
            for session in base_sessions:
                for i in range(5):
                    sessions.append(f"{session.strip()}_{i}")

        proxy_strings = [
            f"{self.proxy_credentials['host']}:{self.proxy_credentials['port']}"
            f":{self.proxy_credentials['username']}:{self.proxy_credentials['password']}"
            f"_country-{self.config['country_code'].lower()}"
            f"_city-{self.config['city']}"
            f"_session-{session}"
            f"_lifetime-{self.config['lifetime']}"
            f"_streaming-{self.config['streaming']}"
            for session in sessions
        ]

        return proxy_strings

    def clear_ip_history(self) -> None:
        """Clear the history of used IPs."""
        self.used_ips.clear()
        logger.info("Cleared IP history")
