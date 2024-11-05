"""
Test script for validating proxy connections and functionality.
This module provides comprehensive testing of proxy settings, rotations,
and location verification.
"""

import logging
import time
from typing import Dict, Optional
import requests
from proxy_manager import ProxyManager
from ig_client import IgClient
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestProxyConnections:
    """Class to test proxy connections and rotations."""

    def __init__(self, account_id: str = "JK"):
        """Initialize test class with ProxyManager."""
        try:
            self.proxy_manager = ProxyManager()
        except ValueError as e:
            logger.error(f"Failed to initialize ProxyManager: {e}")
            raise
        self.account_id = account_id

    def test_proxy_configuration(self) -> bool:
        """Test proxy configuration and credentials."""
        logger.info("\n=== Testing Proxy Configuration ===")
        try:
            # Verify credentials are loaded
            creds = self.proxy_manager.proxy_credentials
            if not all([creds["username"], creds["password"], creds["base_sessions"]]):
                logger.error("❌ Missing proxy credentials")
                return False

            # Verify base sessions are available
            if len(creds["base_sessions"]) < 1:
                logger.error("❌ No base sessions configured")
                return False

            logger.info("✅ Proxy configuration verified")
            logger.info(f"  Host: {creds['host']}")
            logger.info(f"  Base Sessions: {len(creds['base_sessions'])}")
            return True

        except Exception as e:
            logger.error(f"Proxy configuration test failed: {e}")
            return False

    def test_proxy_rotation(self, rotations: int = 6, max_retries: int = 3) -> bool:
        """
        Test proxy rotation functionality with duplicate prevention.

        Args:
            rotations (int): Number of rotations to test
            max_retries (int): Maximum number of retry attempts per rotation

        Returns:
            bool: True if all rotations are successful
        """
        logger.info(f"\n=== Testing Proxy Rotation ({rotations} times) ===")
        previous_ips = set()
        successful_rotations = 0

        try:
            for i in range(rotations):
                logger.info(f"\nRotation {i + 1}/{rotations}")

                for attempt in range(max_retries):
                    # Force rotation
                    self.proxy_manager._load_and_set_proxy()

                    # Check new IP
                    response = requests.get(
                        "http://ip-api.com/json",
                        proxies=self.proxy_manager.get_current_proxies(),
                        timeout=30,
                    )
                    data = response.json()
                    current_ip = data.get("query")

                    if current_ip not in previous_ips:
                        logger.info(f"✅ New IP: {current_ip}")
                        logger.info(
                            f"   Location: {data.get('city')}, {data.get('country')}"
                        )
                        previous_ips.add(current_ip)
                        successful_rotations += 1
                        time.sleep(3)  # Increased delay between successful rotations
                        break
                    else:
                        logger.warning(
                            f"⚠️ Duplicate IP {current_ip} detected, retrying... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(2)  # Wait before retry
                else:
                    logger.error(
                        f"❌ Failed to get unique IP after {max_retries} attempts"
                    )
                    return False

            logger.info(
                f"\n✅ Completed {successful_rotations}/{rotations} successful unique rotations"
            )
            return successful_rotations == rotations

        except Exception as e:
            logger.error(f"Proxy rotation test failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all proxy tests and return results."""
        results = {}

        # Configuration test
        results["proxy_configuration"] = self.test_proxy_configuration()
        if not results["proxy_configuration"]:
            logger.error("❌ Skipping remaining tests due to configuration failure")
            return results

        # Basic connection test
        try:
            proxies = self.proxy_manager.get_current_proxies()
            if not proxies:
                logger.error("❌ No proxy connection available")
                results["basic_connection"] = False
            else:
                response = requests.get(
                    "http://ip-api.com/json", proxies=proxies, timeout=30
                )
                results["basic_connection"] = response.status_code == 200
                logger.info(
                    f"✅ Basic connection test successful: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Basic connection test failed: {e}")
            results["basic_connection"] = False

        # Only continue if basic connection works
        if not results["basic_connection"]:
            logger.error("❌ Skipping remaining tests due to connection failure")
            return results

        # Location verification
        results["location_verification"] = self.proxy_manager.validate_connection()

        # Proxy rotation
        results["proxy_rotation"] = self.test_proxy_rotation()

        return results


def main():
    """Main execution function."""
    tester = TestProxyConnections()
    tester.test_proxy_rotation(rotations=10)
    results = tester.run_all_tests()

    # Print summary
    logger.info("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    # Save results
    try:
        output_dir = Path("test_results")
        output_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"proxy_test_results_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"\nTest results saved to: {output_file}")

    except Exception as e:
        logger.error(f"Failed to save test results: {e}")

    # Overall status
    if all(results.values()):
        logger.info("\n✅ All tests passed successfully!")
    else:
        logger.error("\n❌ Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    main()
