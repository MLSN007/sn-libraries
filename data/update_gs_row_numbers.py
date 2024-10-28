"""
Update existing content records with their Google Sheet row numbers.
"""

import sqlite3
import logging
from google_sheets_handler import GoogleSheetsHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_gs_row_numbers(account_id: str):
    # Connect to database

    account_id = "JK"  # TODO: make this dynamic

    db_path = f"C:/Users/manue/Documents/GitHub007/sn-libraries/data/{account_id}_ig.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Initialize Google Sheets handler
    gs_handler = GoogleSheetsHandler(account_id)
    gs_handler.authenticate()

    try:
        # Get data from Google Sheet
        data = gs_handler.read_spreadsheet(gs_handler.spreadsheet_id, "A:S")
        if not data:
            logger.error("No data found in Google Sheet")
            return

        # Create mapping of content identifiers to row numbers
        content_map = {}
        for row_idx, row in enumerate(
            data[1:], start=2
        ):  # Start from 2 to account for header
            # Use appropriate columns to match content (e.g., title, caption, publish_date)
            key = f"{row[2]}_{row[3]}_{row[11]}"  # Adjust indices based on your sheet structure
            content_map[key] = row_idx

        # Update database records
        cursor.execute(
            "SELECT content_id, title, caption, publish_date FROM content WHERE gs_row_number IS NULL"
        )
        for content in cursor.fetchall():
            content_id, title, caption, publish_date = content
            key = f"{title}_{caption}_{publish_date}"
            if key in content_map:
                cursor.execute(
                    "UPDATE content SET gs_row_number = ? WHERE content_id = ?",
                    (content_map[key], content_id),
                )
                logger.info(
                    f"Updated content_id {content_id} with row number {content_map[key]}"
                )

        conn.commit()
        logger.info("Finished updating Google Sheet row numbers")

    except Exception as e:
        logger.error(f"Error updating row numbers: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    update_gs_row_numbers("JK")  # Replace with your account ID
