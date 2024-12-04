"""
IPRoyal Proxy Manager - Handles proxy configuration, rotation, and connection management.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List, Set
import time
import random
import logging
import requests
from collections import deque
import os
from dotenv import load_dotenv
import uuid

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """Configuration dataclass for IPRoyal proxy settings."""
    username: str
    password: str
    host: str
    port: str
    country: str
    city: str
    session_type: str
    lifetime: str
    protocol: str
    streaming: str
    
class IPRoyalProxyManager:
    """Manages IPRoyal proxy connections, rotation, and validation."""
    
    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize the IPRoyal proxy manager.
        
        Args:
            config_path: Optional path to .env file
        """
        self._load_configuration(config_path)
        self._initialize_manager()
        
    def _load_configuration(self, config_path: Optional[Path]) -> None:
        """Load and validate proxy configuration."""
        load_dotenv(dotenv_path=config_path)
        
        self.config = ProxyConfig(
            username=os.getenv('IPROYAL_USERNAME'),
            password=os.getenv('IPROYAL_PASSWORD'),
            host=os.getenv('IPROYAL_HOST', 'geo.iproyal.com'),
            port=os.getenv('IPROYAL_PORT', '32325'),
            country=os.getenv('IPROYAL_COUNTRY', 'es'),
            city=os.getenv('IPROYAL_CITY', 'madrid'),
            session_type=os.getenv('IPROYAL_SESSION_TYPE', 'sticky_ip'),
            lifetime=os.getenv('IPROYAL_LIFETIME', '1h'),
            protocol=os.getenv('IPROYAL_PROTOCOL', 'http'),
            streaming=os.getenv('IPROYAL_STREAMING', '1')
        )
        
        self._validate_configuration()
        
    def _validate_configuration(self) -> None:
        """Validate required proxy configuration."""
        if not all([self.config.username, self.config.password]):
            raise ValueError("Missing required IPRoyal credentials")
            
    def _initialize_manager(self) -> None:
        """Initialize proxy manager state."""
        self.rotation_interval = int(os.getenv('IPROYAL_ROTATION_INTERVAL', '1500'))
        self.max_retries = int(os.getenv('IPROYAL_MAX_RETRIES', '3'))
        self.last_rotation = time.time()
        self.used_ips: Set[str] = set()
        self.current_session: Optional[str] = None
        self.current_proxy: Optional[Dict[str, str]] = None
        
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for IPRoyal."""
        return uuid.uuid4().hex[:8]
        
    def _format_proxy_string(self, session_id: Optional[str] = None) -> str:
        """
        Format proxy string according to IPRoyal specifications.
        
        Args:
            session_id: Optional session identifier
            
        Returns:
            Formatted proxy string
        """
        if not session_id:
            session_id = self._generate_session_id()
            
        self.current_session = session_id
        
        # Format exactly as shown in proxy_list.txt:
        # host:port:username:password_country-{country}_city-{city}_session-{session}_lifetime-{lifetime}_streaming-{streaming}
        proxy_string = (
            f"{self.config.host}:{self.config.port}:{self.config.username}:"
            f"{self.config.password}_country-{self.config.country}_"
            f"city-{self.config.city}_session-{session_id}_"
            f"lifetime-{self.config.lifetime}_streaming-{self.config.streaming}"
        )
        
        return proxy_string
        
    def get_proxy_dict(self) -> Dict[str, str]:
        """
        Get proxy dictionary for requests library.
        
        Returns:
            Dictionary with proxy configuration
        """
        if not self.current_proxy:
            self.rotate_proxy()
            
        return self.current_proxy

    def rotate_proxy(self, force: bool = False) -> Dict[str, str]:
        """
        Rotate to a new proxy if needed or forced.
        
        Args:
            force: Force rotation regardless of timing
            
        Returns:
            New proxy configuration dictionary
        """
        should_rotate = force or (time.time() - self.last_rotation) >= self.rotation_interval
        
        if should_rotate or not self.current_proxy:
            proxy_string = self._format_proxy_string()
            
            # The proxy string should be used directly without http:// prefix
            self.current_proxy = {
                'http': proxy_string,
                'https': proxy_string
            }
            
            self.last_rotation = time.time()
            logger.info(f"Rotated to new proxy session: {self.current_session}")
            
        return self.current_proxy

    def validate_connection(self, timeout: int = 30) -> bool:
        """
        Validate current proxy connection.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            True if connection is valid
        """
        try:
            proxies = self.get_proxy_dict()
            logger.debug("Attempting connection with proxy configuration: %s", proxies)
            
            response = requests.get(
                'http://ip-api.com/json',
                proxies=proxies,
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                current_ip = data.get('query')
                
                if current_ip in self.used_ips:
                    logger.warning(f"Duplicate IP detected: {current_ip}")
                    return False
                    
                self.used_ips.add(current_ip)
                logger.info(
                    f"Valid connection established - IP: {current_ip}, "
                    f"Location: {data.get('city')}, {data.get('country')}"
                )
                return True
                
        except requests.exceptions.RequestException as e:
            logger.error("Connection validation failed with error: %s", str(e))
            logger.debug("Full exception details:", exc_info=True)
            
        return False

    def get_new_valid_connection(self) -> Optional[Dict[str, str]]:
        """
        Attempt to get a new valid proxy connection.
        
        Returns:
            Valid proxy configuration or None if all attempts fail
        """
        attempts = 0
        while attempts < self.max_retries:
            self.rotate_proxy(force=True)
            if self.validate_connection():
                return self.current_proxy
                
            attempts += 1
            time.sleep(1)
            
        logger.error(f"Failed to obtain valid connection after {self.max_retries} attempts")
        return None

    def clear_ip_history(self) -> None:
        """Clear the history of used IPs."""
        self.used_ips.clear()
        logger.info("Cleared IP history")