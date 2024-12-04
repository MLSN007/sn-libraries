"""
Enhanced IPRoyal Proxy Manager with Dynamic Session Creation and Social Network Support
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List, Set, Literal
import time
import random
import logging
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import uuid
import json
from enum import Enum

logger = logging.getLogger(__name__)

class SocialPlatform(Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

@dataclass
class SessionConfig:
    """Configuration for platform-specific proxy sessions."""
    platform: SocialPlatform
    min_session_time: int  # minimum time in seconds
    max_session_time: int  # maximum time in seconds
    max_requests: int      # maximum requests per session
    country_codes: List[str]  # allowed country codes
    cities: Optional[List[str]] = None  # optional city restrictions

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

    @classmethod
    def from_env(cls, config_path: Optional[Path] = None) -> 'ProxyConfig':
        """Create ProxyConfig from environment variables."""
        load_dotenv(dotenv_path=config_path)
        return cls(
            username=os.getenv('IPROYAL_USERNAME'),
            password=os.getenv('IPROYAL_PASSWORD'),
            host=os.getenv('IPROYAL_HOST', 'geo.iproyal.com'),
            port=os.getenv('IPROYAL_PORT', '12321'),
            country=os.getenv('IPROYAL_COUNTRY', 'es'),
            city=os.getenv('IPROYAL_CITY', 'madrid'),
            session_type=os.getenv('IPROYAL_SESSION_TYPE', 'sticky_ip'),
            lifetime=os.getenv('IPROYAL_LIFETIME', '1h'),
            protocol=os.getenv('IPROYAL_PROTOCOL', 'http'),
            streaming=os.getenv('IPROYAL_STREAMING', '1')
        )

class ProxySession:
    """Manages individual proxy sessions."""
    
    def __init__(self, session_id: str, platform: SocialPlatform, proxy_string: str):
        self.session_id = session_id
        self.platform = platform
        self.proxy_string = proxy_string
        self.start_time = datetime.now()
        self.request_count = 0
        self.last_request = None
        self.ip_address = None
        
    def increment_requests(self) -> None:
        """Increment request counter and update last request timestamp."""
        self.request_count += 1
        self.last_request = datetime.now()
        
    def session_age(self) -> timedelta:
        """Get session age."""
        return datetime.now() - self.start_time
        
    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'platform': self.platform.value,
            'start_time': self.start_time.isoformat(),
            'request_count': self.request_count,
            'last_request': self.last_request.isoformat() if self.last_request else None,
            'ip_address': self.ip_address,
            'age_seconds': self.session_age().total_seconds()
        }

class IPRoyalProxyManager:
    """Enhanced IPRoyal proxy manager with dynamic session creation."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the proxy manager."""
        self.config = ProxyConfig.from_env(config_path)
        self._validate_configuration()
        self._initialize_manager()
        self._load_platform_configs()
        
    def _validate_configuration(self) -> None:
        """Validate required proxy configuration."""
        if not all([self.config.username, self.config.password]):
            raise ValueError("Missing required IPRoyal credentials")
            
    def _initialize_manager(self) -> None:
        """Initialize proxy manager state."""
        self.active_sessions: Dict[str, ProxySession] = {}
        self.used_ips: Set[str] = set()
        self.session_history: List[Dict] = []
        
    def _load_platform_configs(self) -> None:
        """Load platform-specific configurations."""
        self.platform_configs = {
            SocialPlatform.INSTAGRAM: SessionConfig(
                platform=SocialPlatform.INSTAGRAM,
                min_session_time=1800,  # 30 minutes
                max_session_time=3600,  # 1 hour
                max_requests=100,
                country_codes=['us', 'uk', 'ca', 'au'],
                cities=None
            ),
            SocialPlatform.FACEBOOK: SessionConfig(
                platform=SocialPlatform.FACEBOOK,
                min_session_time=3600,  # 1 hour
                max_session_time=7200,  # 2 hours
                max_requests=200,
                country_codes=['us', 'uk', 'ca', 'de', 'fr'],
                cities=None
            ),
            # Add other platform configs...
        }
        
    def create_session(self, platform: SocialPlatform) -> ProxySession:
        """Create a new proxy session for specific platform."""
        session_id = uuid.uuid4().hex[:8]
        platform_config = self.platform_configs[platform]
        
        # Select country and city based on platform config
        country = random.choice(platform_config.country_codes)
        city = random.choice(platform_config.cities) if platform_config.cities else None
        
        proxy_string = self._format_proxy_string(session_id, country, city)
        session = ProxySession(session_id, platform, proxy_string)
        
        self.active_sessions[session_id] = session
        return session
        
    def _format_proxy_string(self, session_id: str, country: str, city: Optional[str]) -> str:
        """Format proxy string with dynamic parameters."""
        base_string = (
            f"{self.config.host}:{self.config.port}:{self.config.username}:"
            f"{self.config.password}_country-{country}"
        )
        
        if city:
            base_string += f"_city-{city}"
            
        base_string += f"_session-{session_id}_lifetime-{self.config.lifetime}_streaming-{self.config.streaming}"
        
        return base_string
        
    def get_session(self, platform: SocialPlatform) -> ProxySession:
        """Get or create a session for the specified platform."""
        # Clean expired sessions
        self._clean_expired_sessions(platform)
        
        # Find suitable existing session
        for session in self.active_sessions.values():
            if (session.platform == platform and 
                session.request_count < self.platform_configs[platform].max_requests):
                return session
                
        # Create new session if none suitable found
        return self.create_session(platform)
        
    def _clean_expired_sessions(self, platform: SocialPlatform) -> None:
        """Clean expired sessions based on platform configuration."""
        platform_config = self.platform_configs[platform]
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if session.platform != platform:
                continue
                
            age_seconds = session.session_age().total_seconds()
            if (age_seconds > platform_config.max_session_time or
                session.request_count >= platform_config.max_requests):
                expired_sessions.append(session_id)
                self.session_history.append(session.to_dict())
                
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            
    def get_proxy_dict(self, platform: SocialPlatform) -> Dict[str, str]:
        """Get proxy dictionary for requests library."""
        session = self.get_session(platform)
        return {
            'http': session.proxy_string,
            'https': session.proxy_string
        }
        
    def validate_session(self, session: ProxySession, timeout: int = 30) -> bool:
        """Validate proxy session connection."""
        try:
            proxies = {
                'http': session.proxy_string,
                'https': session.proxy_string
            }
            
            response = requests.get(
                'http://ip-api.com/json',
                proxies=proxies,
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                ip = data.get('query')
                
                if ip in self.used_ips:
                    logger.warning(f"Duplicate IP detected: {ip}")
                    return False
                    
                session.ip_address = ip
                self.used_ips.add(ip)
                return True
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Session validation failed: {str(e)}")
            
        return False
        
    def rotate_session(self, platform: SocialPlatform, force: bool = False) -> ProxySession:
        """Force rotation to new session."""
        if force:
            return self.create_session(platform)
            
        return self.get_session(platform)
        
    def save_session_history(self, output_path: Path) -> None:
        """Save session history to file."""
        with open(output_path, 'w') as f:
            json.dump(self.session_history, f, indent=2)
            
    def clear_session_history(self) -> None:
        """Clear session history and used IPs."""
        self.session_history.clear()
        self.used_ips.clear()