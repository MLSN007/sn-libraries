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


class ProxyTester:
    """Class to manage proxy testing operations."""

    def __init__(self, account_id: str = "JK"):
        """
        Initialize the proxy tester.

        Args:
            account_id (str): Instagram account identifier for testing
        """
        self.account_id = account_id
        self.proxy_manager = ProxyManager()
        self.ig_client = IgClient(account_id)

    def test_basic_connection(self) -> bool:
        """
        Test basic proxy connection using a simple IP check.

        Returns:
            bool: True if connection is successful
        """
        logger.info("\n=== Testing Basic Connection ===")
        try:
            proxies = self.proxy_manager.get_current_proxies()
            response = requests.get(
                "http://ip-api.com/json", proxies=proxies, timeout=30
            )
            data = response.json()

            logger.info("Connection Details:")
            logger.info(f"  IP Address: {data.get('query', 'Unknown')}")
            logger.info(
                f"  Location: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
            )
            logger.info(f"  ISP: {data.get('isp', 'Unknown')}")

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Basic connection test failed: {e}")
            return False

    def test_location_verification(self) -> bool:
        """
        Verify that the proxy is providing an IP from the correct location.

        Returns:
            bool: True if location matches configuration
        """
        logger.info("\n=== Testing Location Verification ===")
        try:
            if not self.proxy_manager.validate_connection():
                logger.error("❌ Location verification failed")
                return False

            logger.info("✅ Location verified successfully")
            return True

        except Exception as e:
            logger.error(f"Location verification failed: {e}")
            return False

    def test_proxy_rotation(self, rotations: int = 3) -> bool:
        """
        Test proxy rotation functionality.

        Args:
            rotations (int): Number of rotations to test

        Returns:
            bool: True if all rotations are successful
        """
        logger.info(f"\n=== Testing Proxy Rotation ({rotations} times) ===")
        previous_ips = set()

        try:
            for i in range(rotations):
                logger.info(f"\nRotation {i + 1}/{rotations}")

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

                if current_ip in previous_ips:
                    logger.warning(f"⚠️ IP {current_ip} was already used")
                else:
                    logger.info(f"✅ New IP: {current_ip}")
                    logger.info(
                        f"   Location: {data.get('city')}, {data.get('country')}"
                    )

                previous_ips.add(current_ip)
                time.sleep(2)  # Small delay between rotations

            return True

        except Exception as e:
            logger.error(f"Proxy rotation test failed: {e}")
            return False

    def test_instagram_connection(self) -> bool:
        """
        Test Instagram connection through proxy.

        Returns:
            bool: True if Instagram connection is successful
        """
        logger.info("\n=== Testing Instagram Connection ===")
        try:
            if self.ig_client.validate_session():
                logger.info("✅ Instagram connection successful")
                return True
            else:
                logger.error("❌ Instagram connection failed")
                return False

        except Exception as e:
            logger.error(f"Instagram connection test failed: {e}")
            return False

    def save_test_results(self, results: Dict[str, bool]) -> None:
        """
        Save test results to a JSON file.

        Args:
            results (Dict[str, bool]): Dictionary of test results
        """
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


def run_all_tests(account_id: str = "JK") -> None:
    """
    Run all proxy tests and save results.

    Args:
        account_id (str): Instagram account identifier for testing
    """
    tester = ProxyTester(account_id)
    results = {}

    logger.info("Starting proxy connection tests...")

    # Run all tests
    results["basic_connection"] = tester.test_basic_connection()
    results["location_verification"] = tester.test_location_verification()
    results["proxy_rotation"] = tester.test_proxy_rotation(rotations=8)

    # ---------------------------------------------------------------------------
    # results['instagram_connection'] = tester.test_instagram_connection()
    # ---------------------------------------------------------------------------

    # Print summary
    logger.info("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    # Save results
    tester.save_test_results(results)

    # Overall status
    if all(results.values()):
        logger.info("\n✅ All tests passed successfully!")
    else:
        logger.error("\n❌ Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    run_all_tests()
