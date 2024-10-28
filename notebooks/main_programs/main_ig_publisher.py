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
from ig_client import IgClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Process pending Instagram content')
    parser.add_argument('account_id', help='Instagram account identifier (e.g., JK)')
    parser.add_argument('--force', action='store_true', help='Skip safety confirmation')
    parser.add_argument('--reset-session', action='store_true', 
                       help='Reset Instagram session before proceeding')
    
    args = parser.parse_args()

    try:
        # Handle session reset if requested
        if args.reset_session:
            logger.info("Attempting to reset Instagram session...")
            client = IgClient(args.account_id)
            if client.reset_session():
                logger.info("✅ Successfully reset session")
            else:
                logger.error("❌ Failed to reset session")
                return

        while True:  # Main loop
            if not args.force:
                response = input("\n⚠️  WARNING: This will access Instagram API. Continue? (y/N/q): ").lower()
                if response == 'q':
                    logger.info("Exiting program...")
                    sys.exit(0)
                elif response != 'y':
                    logger.info("Operation cancelled by user")
                    return

            publisher = IgContentPublisher(args.account_id)
            publisher.process_pending_content()
            
            # Ask if user wants to continue
            continue_response = input("\nDo you want to process more content? (y/N): ").lower()
            if continue_response != 'y':
                logger.info("Exiting program...")
                break

    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running content publisher: {e}")
        raise

if __name__ == "__main__":
    main()
