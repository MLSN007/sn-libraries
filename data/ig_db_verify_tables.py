"""
Verify that all tables exist in the database.
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_tables():
    conn = sqlite3.connect(r"C:\Users\manue\Documents\GitHub007\sn-libraries\data\JK_ig.db")
    cursor = conn.cursor()
    
    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    logger.info("Tables in database:")
    for table in tables:
        logger.info(f"- {table[0]}")
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            logger.info(f"  - {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    verify_tables()
