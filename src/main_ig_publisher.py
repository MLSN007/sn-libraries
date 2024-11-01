"""
Main script for running the Instagram content publisher.
"""

import logging
import argparse
from ig_content_publisher import IgContentPublisher

# Add this filter class
class NoHTMLFilter(logging.Filter):
    def filter(self, record):
        return not (record.msg.startswith('<') or 
                   'script' in str(record.msg) or 
                   'html' in str(record.msg).lower())

# Modify the logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add filter to root logger
logging.getLogger().addFilter(NoHTMLFilter())

logger = logging.getLogger(__name__)

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Process pending Instagram content')
    
    # Required argument: account_id
    parser.add_argument('account_id', 
                       help='Instagram account identifier (e.g., JK)')
    
    # Optional argument: --force
    parser.add_argument('--force', 
                       action='store_true',
                       help='Skip safety confirmation and proceed with publishing')
    
    args = parser.parse_args()

    try:
        # If not using --force, ask for confirmation
        if not args.force:
            confirm = input("\n⚠️  WARNING: This will access Instagram API. Continue? (y/N): ")
            if confirm.lower() != 'y':
                logger.info("Operation cancelled by user")
                return

        # Create publisher instance and process content
        publisher = IgContentPublisher(args.account_id)
        publisher.process_pending_content()
        
    except Exception as e:
        logger.error(f"Error running content publisher: {e}")
        raise

if __name__ == "__main__":
    main()
