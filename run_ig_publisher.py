"""
Script to run Instagram publishing workflow.
"""
import os
import sqlite3
import argparse
import logging
from typing import Optional

def add_error_column(db_path: str) -> None:
    """Add error_message column if it doesn't exist."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(content)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'error_message' not in columns:
            cursor.execute("ALTER TABLE content ADD COLUMN error_message TEXT")
            logging.info("Added error_message column to content table")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error adding column: {e}")
        raise

def run_workflow(account_id: str, sync_only: bool = False) -> None:
    """Run the complete workflow."""
    try:
        # 1. Add error column
        db_path = f"data/{account_id}_ig.db"
        add_error_column(db_path)
        
        # 2. Sync with Google Sheet
        from notebooks.main_programs.main_ig_gs_handling import main as sync_main
        logging.info("Starting Google Sheet sync...")
        sync_main()
        
        # 3. Publish content (if not sync_only)
        if not sync_only:
            from notebooks.main_programs.main_ig_publisher import main as publish_main
            logging.info("Starting content publishing...")
            publish_main()
            
    except Exception as e:
        logging.error(f"Workflow error: {e}")
        raise

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Run Instagram publishing workflow')
    parser.add_argument('account_id', help='Account ID (e.g., JK)')
    parser.add_argument('--sync-only', action='store_true', 
                       help='Only sync with Google Sheet, no publishing')
    
    args = parser.parse_args()
    
    # Run workflow
    run_workflow(args.account_id, args.sync_only)

if __name__ == "__main__":
    main() 