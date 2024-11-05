"""Configuration management for the application."""

import os
from dotenv import load_dotenv
from typing import Dict, Optional

class Config:
    """Central configuration management."""
    
    def __init__(self):
        load_dotenv()
        
        # Proxy Configuration
        self.proxy = {
            "host": os.getenv("PROXY_HOST"),
            "port": os.getenv("PROXY_PORT"),
            "username": os.getenv("PROXY_USERNAME"),
            "password": os.getenv("PROXY_PASSWORD"),
            "base_sessions": os.getenv("PROXY_BASE_SESSIONS", "").split(",")
        }
        
        # Location Configuration
        self.location = {
            "country_code": "ES",  # Can be overridden
            "country_name": "Spain",
            "city": "huelva",
            "lifetime": "30m",
            "streaming": "1"
        }
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration."""
        if not all([
            self.proxy["host"],
            self.proxy["port"],
            self.proxy["username"],
            self.proxy["password"],
            self.proxy["base_sessions"]
        ]):
            raise ValueError("Missing required proxy configuration in .env file") 