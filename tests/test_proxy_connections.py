"""
Enhanced testing module for IPRoyal Dynamic Proxy Manager
"""

import json
import logging
import os
import time
from typing import Dict, Optional, List
from pathlib import Path
from datetime import datetime
import requests
from dataclasses import asdict

from proxy_services import (
    IPRoyalProxyManager,
    SocialPlatform,
    ProxySession,
    SessionConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'proxy_tests_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

class IPRoyalDynamicTester:
    """Test suite for Dynamic Proxy Manager."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize tester with configuration."""
        self.proxy_manager = IPRoyalProxyManager(config_path)
        self.test_results: List[Dict] = []
        
    def test_instagram_session(self) -> Dict:
        """Test Instagram-specific proxy session."""
        logger.info("\n=== Testing Instagram Session ===")
        start_time = time.time()
        
        try:
            # Create Instagram session
            session = self.proxy_manager.create_session(SocialPlatform.INSTAGRAM)
            
            # Validate session
            is_valid = self.proxy_manager.validate_session(session)
            
            # Test multiple requests
            for i in range(5):
                session.increment_requests()
                time.sleep(1)
                
            details = {
                'session_id': session.session_id,
                'ip_address': session.ip_address,
                'request_count': session.request_count,
                'session_age': session.session_age().total_seconds(),
                'is_valid': is_valid
            }
            
            return {
                'name': 'instagram_session',
                'success': is_valid,
                'details': details,
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Instagram session test failed: {str(e)}")
            return {
                'name': 'instagram_session',
                'success': False,
                'details': {'error': str(e)},
                'duration': time.time() - start_time
            }
            
    def test_session_rotation(self) -> Dict:
        """Test session rotation for multiple platforms."""
        logger.info("\n=== Testing Session Rotation ===")
        start_time = time.time()
        results = []
        
        try:
            platforms = [SocialPlatform.INSTAGRAM, SocialPlatform.FACEBOOK]
            
            for platform in platforms:
                # Create multiple sessions
                sessions = []
                for _ in range(3):
                    session = self.proxy_manager.rotate_session(platform, force=True)
                    is_valid = self.proxy_manager.validate_session(session)
                    sessions.append({
                        'session_id': session.session_id,
                        'ip_address': session.ip_address,
                        'is_valid': is_valid
                    })
                    time.sleep(2)
                    
                results.append({
                    'platform': platform.value,
                    'sessions': sessions
                })
                
            return {
                'name': 'session_rotation',
                'success': all(s['is_valid'] for r in results for s in r['sessions']),
                'details': results,
                'duration': time.time() - start_time
            }
            
        except Exception as e:
            logger.error("Session rotation test failed: %s", str(e))
            return {
                'name': 'session_rotation', 
                'success': False,
                'details': {'error': str(e)},
                'duration': time.time() - start_time
            }