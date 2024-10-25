"""
Main script for running the Instagram content publisher.
"""

import logging
import argparse
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)

from ig_content_publisher import IgContentPublisher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Process pending Instagram content')
    parser.add_argument('account_id', help='Instagram account identifier (e.g., JK)')
    parser.add_argument('--force', action='store_true', help='Skip safety confirmation')
    
    args = parser.parse_args()

    try:
        if not args.force:
            confirm = input("\n⚠️  WARNING: This will access Instagram API. Continue? (y/N): ")
            if confirm.lower() != 'y':
                logger.info("Operation cancelled by user")
                return

        publisher = IgContentPublisher(args.account_id)
        publisher.process_pending_content()
    except Exception as e:
        logger.error(f"Error running content publisher: {e}")
        raise

if __name__ == "__main__":
    main()
