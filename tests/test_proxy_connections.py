"""
Test script for validating proxy connections and functionality.
This module provides comprehensive testing of proxy settings, rotations,
and location verification.
"""

import json
import logging
import os
import time
from typing import Dict, Optional, Set
from pathlib import Path
from dotenv import load_dotenv
import requests
from sn_libraries import ProxyManager
from sn_libraries import IgClient


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProxyTester:
    """Class to manage proxy testing operations."""

    def __init__(self, account_id: str = "JK") -> None:
        """
        Initialize the proxy tester.

        Args:
            account_id (str): Instagram account identifier for testing.
        """
        self.account_id: str = account_id
        self.proxy_manager: ProxyManager = ProxyManager()
        self.ig_client: IgClient = IgClient(account_id)
        self.rotations: int = int(os.getenv("PROXY_ROTATIONS", 3))
        logger.info("Configured to perform %d proxy rotations", self.rotations)

    def test_basic_connection(self) -> bool:
        """
        Test basic proxy connection using a simple IP check.

        Returns:
            bool: True if connection is successful, False otherwise.
        """
        logger.info("\n=== Testing Basic Connection ===")
        try:
            proxies: Dict[str, str] = self.proxy_manager.get_current_proxies()
            response: requests.Response = requests.get(
                "http://ip-api.com/json", proxies=proxies, timeout=30
            )
            data: Dict = response.json()

            logger.info("Connection Details:")
            logger.info("  IP Address: %s", data.get("query", "Unknown"))
            logger.info(
                "  Location: %s, %s",
                data.get("city", "Unknown"),
                data.get("country", "Unknown"),
            )
            logger.info("  ISP: %s", data.get("isp", "Unknown"))

            return response.status_code == 200

        except Exception as e:
            logger.error("Basic connection test failed: %s", e)
            return False

    def test_location_verification(self) -> bool:
        """
        Verify that the proxy is providing an IP from the correct location.

        Returns:
            bool: True if location matches configuration, False otherwise.
        """
        logger.info("\n=== Testing Location Verification ===")
        try:
            if not self.proxy_manager.validate_connection():
                logger.error("❌ Location verification failed")
                return False

            logger.info("✅ Location verified successfully")
            return True

        except Exception as e:
            logger.error("Location verification failed: %s", e)
            return False

    def test_proxy_rotation(self, rotations: int = 3) -> bool:
        """
        Test proxy rotation functionality.

        Args:
            rotations (int): Number of rotations to test.

        Returns:
            bool: True if all rotations are successful, False otherwise.
        """
        logger.info("\n=== Testing Proxy Rotation (%d times) ===", rotations)
        previous_ips: Set[str] = set()

        try:
            for i in range(rotations):
                logger.info("\nRotation %d/%d", i + 1, rotations)

                # Force rotation
                if not self.proxy_manager._load_and_set_proxy():
                    logger.error("❌ Failed to rotate proxy")
                    return False

                # Check new IP
                proxies: Dict[str, str] = self.proxy_manager.get_current_proxies()
                response: requests.Response = requests.get(
                    "http://ip-api.com/json",
                    proxies=proxies,
                    timeout=30,
                )
                data: Dict = response.json()
                current_ip: str = data.get("query", "Unknown")

                if current_ip in previous_ips:
                    logger.warning("⚠️ IP %s was already used", current_ip)
                else:
                    logger.info("✅ New IP: %s", current_ip)
                    logger.info(
                        "   Location: %s, %s",
                        data.get("city", "Unknown"),
                        data.get("country", "Unknown"),
                    )

                previous_ips.add(current_ip)
                time.sleep(2)  # Small delay between rotations

            return True

        except Exception as e:
            logger.error("Proxy rotation test failed: %s", e)
            return False

    def test_instagram_connection(self) -> bool:
        """
        Test Instagram connection through proxy.

        Returns:
            bool: True if Instagram connection is successful, False otherwise.
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
            logger.error("Instagram connection test failed: %s", e)
            return False

    def save_test_results(self, results: Dict[str, bool]) -> None:
        """
        Save test results to a JSON file.

        Args:
            results (Dict[str, bool]): Dictionary of test results.
        """
        try:
            output_dir: Path = Path("test_results")
            output_dir.mkdir(exist_ok=True)

            timestamp: str = time.strftime("%Y%m%d_%H%M%S")
            output_file: Path = output_dir / f"proxy_test_results_{timestamp}.json"

            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)

            logger.info("\nTest results saved to: %s", output_file)

        except Exception as e:
            logger.error("Failed to save test results: %s", e)


def run_all_tests(account_id: str = "JK") -> None:
    """
    Run all proxy tests and save results.

    Args:
        account_id (str): Instagram account identifier for testing.
    """
    tester: ProxyTester = ProxyTester(account_id)
    results: Dict[str, bool] = {}

    logger.info("Starting proxy connection tests...")

    # Run all tests
    results["basic_connection"] = tester.test_basic_connection()
    results["location_verification"] = tester.test_location_verification()
    results["proxy_rotation"] = tester.test_proxy_rotation(rotations=tester.rotations)

    # ---------------------------------------------------------------------------
    # results['instagram_connection'] = tester.test_instagram_connection()
    # ---------------------------------------------------------------------------

    # Print summary
    logger.info("\n=== Test Results Summary ===")
    for test_name, result in results.items():
        status: str = "✅ PASSED" if result else "❌ FAILED"
        logger.info("%s: %s", test_name, status)

    # Save results
    tester.save_test_results(results)

    # Overall status
    if all(results.values()):
        logger.info("\n✅ All tests passed successfully!")
    else:
        logger.error("\n❌ Some tests failed. Check the logs for details.")


if __name__ == "__main__":
    run_all_tests()
