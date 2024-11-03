"""
Utility script to reset Instagram session.
"""

import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Add the src directory to Python path
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from ig_client import IgClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Device configurations for different regions/devices
DEVICE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "samsung_s23_ultra": {
        "app_version": "300.0.0.0.0",
        "android_version": "34",
        "android_release": "14.0",
        "device_model": "SM-S918B",
        "device": "b0s",
        "cpu": "exynos2200",
        "manufacturer": "SAMSUNG",
    },
    "iphone_15_pro": {
        "app_version": "300.0.0.0.0",
        "device_model": "iPhone15,3",
        "device": "iPhone",
        "manufacturer": "Apple",
    },
    "pixel_8_pro": {
        "app_version": "300.0.0.0.0",
        "android_version": "14",
        "android_release": "14.0",
        "device_model": "Pixel 8 Pro",
        "device": "husky",
        "cpu": "tensor",
        "manufacturer": "Google",
    },
}

# Region configurations
REGION_CONFIGS = {
    "ES": {"locale": "es_ES", "timezone_offset": "3600"},  # Spain
    # Commented out regions that don't apply to current setup
    # "US": {"locale": "en_US", "timezone_offset": "-14400"},  # USA Eastern
    # "UK": {"locale": "en_GB", "timezone_offset": "0"},  # United Kingdom
}


def main():
    parser = argparse.ArgumentParser(description="Reset Instagram session")
    parser.add_argument("account_id", help="Instagram account identifier (e.g., JK)")
    parser.add_argument(
        "--device",
        choices=list(DEVICE_CONFIGS.keys()),
        default="samsung_s23_ultra",
        help="Device configuration to use",
    )
    parser.add_argument(
        "--region",
        choices=list(REGION_CONFIGS.keys()),
        default="ES",
        help="Region configuration to use",
    )

    args = parser.parse_args()

    try:
        logger.info(
            f"Attempting to reset Instagram session for account: {args.account_id}"
        )
        logger.info(f"Using device configuration: {args.device}")
        logger.info(f"Using region configuration: {args.region}")

        # Combine device and region settings
        device_settings = DEVICE_CONFIGS[args.device].copy()
        device_settings.update(REGION_CONFIGS[args.region])

        # Initialize client with custom settings
        client = IgClient(args.account_id)
        client.client.set_device(device_settings)

        if client.reset_session():
            logger.info("✅ Successfully reset session with new device settings")
            logger.info(f"Device: {device_settings['device_model']}")
            logger.info(f"Region: {device_settings['locale']}")
        else:
            logger.error("❌ Failed to reset session")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
