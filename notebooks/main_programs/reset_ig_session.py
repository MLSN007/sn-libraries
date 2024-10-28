"""
Utility script to reset Instagram session.
"""

import logging
import argparse
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from ig_client import IgClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Reset Instagram session')
    parser.add_argument('account_id', help='Instagram account identifier (e.g., JK)')
    
    args = parser.parse_args()

    try:
        logger.info(f"Attempting to reset Instagram session for account: {args.account_id}")
        client = IgClient(args.account_id)
        if client.reset_session():
            logger.info("✅ Successfully reset session")
        else:
            logger.error("❌ Failed to reset session")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
