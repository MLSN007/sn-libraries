"""
IPRoyal Proxy Service Testing Module

This module provides comprehensive testing of IPRoyal proxy settings, rotations,
and location verification using the improved IPRoyalProxyManager.
"""

import json
import logging
import os
import time
from typing import Dict, Optional, Set, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import requests
from dotenv import load_dotenv

from proxy_services import IPRoyalProxyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"proxy_tests_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Data class for storing test results."""
    name: str
    success: bool
    details: Dict
    duration: float  # Test duration in seconds
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict:
        """Convert TestResult to dictionary format."""
        result_dict = asdict(self)
        result_dict['timestamp'] = self.timestamp.isoformat()
        return result_dict

class IPRoyalProxyTester:
    """Class to manage IPRoyal proxy testing operations."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize the proxy tester.

        Args:
            config_path: Optional path to configuration file
        """
        self.proxy_manager = IPRoyalProxyManager(config_path)
        self.rotations: int = int(os.getenv("IPROYAL_TEST_ROTATIONS", "3"))
        self.test_results: List[TestResult] = []
        self.test_urls = {
            'ip_check': 'http://ip-api.com/json',
            'backup_ip_check': 'https://ipinfo.io/json'
        }
        
        logger.info(f"Initialized IPRoyalProxyTester with {self.rotations} rotations")

    def _make_request(self, url: str, proxies: Dict[str, str], timeout: int = 30) -> requests.Response:
        """
        Make an HTTP request with retry logic.

        Args:
            url: Target URL
            proxies: Proxy configuration
            timeout: Request timeout in seconds

        Returns:
            Response object
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return requests.get(url, proxies=proxies, timeout=timeout)
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def test_basic_connection(self) -> TestResult:
        """Test basic proxy connection using IP check."""
        logger.info("\n=== Testing Basic Connection ===")
        start_time = time.time()
        details = {}
        
        try:
            proxies = self.proxy_manager.get_proxy_dict()
            
            # Try primary IP check service
            try:
                response = self._make_request(self.test_urls['ip_check'], proxies)
                data = response.json()
                service_used = 'ip-api'
            except requests.RequestException:
                # Fallback to backup service
                logger.warning("Primary IP check failed, using backup service")
                response = self._make_request(self.test_urls['backup_ip_check'], proxies)
                data = response.json()
                service_used = 'ipinfo'
            
            details = {
                'service_used': service_used,
                'ip': data.get("ip") or data.get("query", "Unknown"),
                'city': data.get("city", "Unknown"),
                'country': data.get("country", "Unknown"),
                'isp': data.get("org") or data.get("isp", "Unknown"),
                'status_code': response.status_code
            }
            
            success = response.status_code == 200
            logger.info("Connection Details:")
            for key, value in details.items():
                logger.info(f"  {key}: {value}")
                
            return TestResult(
                name="basic_connection",
                success=success,
                details=details,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Basic connection test failed: {str(e)}")
            return TestResult(
                name="basic_connection",
                success=False,
                details={"error": str(e)},
                duration=time.time() - start_time
            )

    def test_location_verification(self) -> TestResult:
        """Verify proxy location matches configuration."""
        logger.info("\n=== Testing Location Verification ===")
        start_time = time.time()
        details = {}
        
        try:
            proxies = self.proxy_manager.get_proxy_dict()
            response = self._make_request(self.test_urls['ip_check'], proxies)
            data = response.json()
            
            expected_country = self.proxy_manager.config.country.upper()
            expected_city = self.proxy_manager.config.city.lower()
            actual_country = data.get("countryCode", "").upper()
            actual_city = data.get("city", "").lower()
            
            location_match = (
                actual_country == expected_country and
                actual_city == expected_city
            )
            
            details = {
                "expected_location": f"{expected_city}, {expected_country}",
                "actual_location": f"{actual_city}, {actual_country}",
                "location_match": location_match,
                "ip": data.get("query", "Unknown")
            }
            
            if location_match:
                logger.info("[OK] Location verified successfully")
            else:
                logger.error("[ERROR] Location verification failed")
                
            return TestResult(
                name="location_verification",
                success=location_match,
                details=details,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Location verification failed: {str(e)}")
            return TestResult(
                name="location_verification",
                success=False,
                details={"error": str(e)},
                duration=time.time() - start_time
            )

    def test_proxy_rotation(self) -> TestResult:
        """Test proxy rotation functionality."""
        logger.info(f"\n=== Testing Proxy Rotation ({self.rotations} times) ===")
        start_time = time.time()
        details = {
            "rotations": [],
            "unique_ips": set(),
            "rotation_times": []
        }
        
        try:
            for i in range(self.rotations):
                rotation_start = time.time()
                logger.info(f"\nRotation {i + 1}/{self.rotations}")
                
                proxies = self.proxy_manager.rotate_proxy(force=True)
                response = self._make_request(self.test_urls['ip_check'], proxies)
                data = response.json()
                
                rotation_time = time.time() - rotation_start
                details["rotation_times"].append(rotation_time)
                
                rotation_info = {
                    "ip": data.get("query", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "country": data.get("country", "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                    "rotation_time": rotation_time
                }
                
                details["rotations"].append(rotation_info)
                details["unique_ips"].add(rotation_info["ip"])
                
                if len(details["unique_ips"]) != len(details["rotations"]):
                    logger.warning("[WARN] IP %s was already used", rotation_info["ip"])
                else:
                    logger.info("[OK] New IP: %s", rotation_info["ip"])
                
                time.sleep(2)  # Small delay between rotations
            
            # Process results
            details["unique_ips"] = list(details["unique_ips"])
            details["avg_rotation_time"] = sum(details["rotation_times"]) / len(details["rotation_times"])
            details["max_rotation_time"] = max(details["rotation_times"])
            details["min_rotation_time"] = min(details["rotation_times"])
            
            success = len(details["unique_ips"]) == self.rotations
            
            return TestResult(
                name="proxy_rotation",
                success=success,
                details=details,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Proxy rotation test failed: {str(e)}")
            return TestResult(
                name="proxy_rotation",
                success=False,
                details={"error": str(e)},
                duration=time.time() - start_time
            )

    def save_test_results(self) -> Path:
        """
        Save test results to a JSON file.
        
        Returns:
            Path to the saved results file
        """
        try:
            output_dir = Path("test_results")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"iproyal_proxy_test_{timestamp}.json"
            
            results_dict = {
                "timestamp": datetime.now().isoformat(),
                "proxy_config": {
                    "host": self.proxy_manager.config.host,
                    "country": self.proxy_manager.config.country,
                    "city": self.proxy_manager.config.city,
                    "rotation_interval": self.proxy_manager.rotation_interval
                },
                "results": [result.to_dict() for result in self.test_results]
            }
            
            with open(output_file, "w") as f:
                json.dump(results_dict, f, indent=2)
                
            logger.info(f"\nTest results saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save test results: {str(e)}")
            raise

def run_proxy_tests(config_path: Optional[Path] = None) -> None:
    """
    Run all IPRoyal proxy tests and save results.
    
    Args:
        config_path: Optional path to configuration file
    """
    tester = IPRoyalProxyTester(config_path)
    
    logger.info("Starting IPRoyal proxy tests...")
    
    # Run tests
    tests = [
        tester.test_basic_connection(),
        tester.test_location_verification(),
        tester.test_proxy_rotation()
    ]
    
    tester.test_results.extend(tests)
    
    # Print summary
    logger.info("\n=== Test Results Summary ===")
    for result in tests:
        status = "[PASSED]" if result.success else "[FAILED]"
        logger.info(f"{result.name}: {status} (Duration: {result.duration:.2f}s)")
    
    # Save results
    tester.save_test_results()
    
    # Overall status
    if all(result.success for result in tests):
        logger.info("\n[SUCCESS] All tests passed successfully!")
    else:
        logger.error("\n[ERROR] Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    run_proxy_tests()