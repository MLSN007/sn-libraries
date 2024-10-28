"""
Manages the publication of Instagram content from SQLite database.

This module handles the scheduling and publishing of Instagram content stored in a SQLite
database, coordinating with Google Drive for media files and using existing Instagram
publishing methods.
"""

import os
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, cast
from io import BytesIO
import time
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload
import tempfile
import shutil
from pathlib import Path
import traceback

from ig_client import IgClient
from ig_post_manager import IgPostManager
from ig_utils import IgUtils
from google_sheets_handler import GoogleSheetsHandler
from instagrapi.types import Location, Media

logger = logging.getLogger(__name__)


class IgContentPublisher:
    """
    Manages the publication of Instagram content from a SQLite database.

    This class handles:
    - Querying pending content from SQLite
    - Retrieving media from Google Drive
    - Publishing content via IgPostManager
    - Updating database status after publishing
    """

    def __init__(self, account_id: str):
        """
        Initialize the content publisher.

        Args:
            account_id (str): The Instagram account identifier
        """
        self.account_id = account_id
        self.db_path = (
            f"C:/Users/manue/Documents/GitHub007/sn-libraries/data/{account_id}_ig.db"
        )
        self.ig_client = IgClient(account_id)
        self.post_manager = IgPostManager(self.ig_client)
        self.gs_handler = GoogleSheetsHandler(account_id)
        self.gs_handler.authenticate()
        
        # Initialize Google Sheet setup
        folder_name = "ig JK tests"  # Make this configurable if needed
        self.folder_id = self.gs_handler.get_folder_id(folder_name)
        if self.folder_id:
            spreadsheet_name = f"{account_id} IG input table"
            self.gs_handler.spreadsheet_id = self.gs_handler.find_file_id(
                self.folder_id, spreadsheet_name
            )
            if not self.gs_handler.spreadsheet_id:
                logger.error(f"Could not find spreadsheet: {spreadsheet_name}")
        else:
            logger.error(f"Could not find folder: {folder_name}")

    def get_pending_content(self) -> List[Dict[str, Any]]:
        """
        Retrieve pending content that is due for publication.

        Returns:
            List[Dict[str, Any]]: List of content items ready to be published
        """
        now = datetime.now()
        logger.info(
            f"Checking for pending content at: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # First, let's check what's in the database regardless of status
        check_query = """
            SELECT content_id, content_type, status, publish_date, publish_time 
            FROM content
        """

        try:
            with sqlite3.connect(self.db_path) as conn:
                logger.info(f"Connected to database: {self.db_path}")
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Check all content first
                cursor.execute(check_query)
                all_content = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Total content in database: {len(all_content)}")
                for content in all_content:
                    # Format time properly
                    time_str = content["publish_time"]
                    if time_str and len(time_str.split(":")) == 3:
                        h, m, s = time_str.split(":")
                        formatted_time = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                    else:
                        formatted_time = "00:00:00"

                    logger.info(
                        f"Content {content['content_id']}: "
                        f"type={content['content_type']}, "
                        f"status={content['status']}, "
                        f"date={content['publish_date']}, "
                        f"time={formatted_time}"
                    )

                # Now get pending content with proper time formatting
                query = """
                    SELECT * FROM content 
                    WHERE status = 'pending' 
                    AND datetime(publish_date || ' ' || 
                        CASE 
                            WHEN publish_time LIKE '_:%' THEN '0' || publish_time
                            ELSE publish_time 
                        END
                    ) <= datetime(?)
                """

                cursor.execute(query, (now.strftime("%Y-%m-%d %H:%M:%S"),))
                pending_content = [dict(row) for row in cursor.fetchall()]

                logger.info(
                    f"Found {len(pending_content)} items with status='pending' and due for publication"
                )

                # Log details of each pending item
                for content in pending_content:
                    # Format time properly for logging
                    time_str = content["publish_time"]
                    if time_str and len(time_str.split(":")) == 3:
                        h, m, s = time_str.split(":")
                        formatted_time = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
                    else:
                        formatted_time = "00:00:00"

                    scheduled_datetime = f"{content['publish_date']} {formatted_time}"
                    logger.info(f"Pending content {content['content_id']}:")
                    logger.info(f"  - Type: {content['content_type']}")
                    logger.info(f"  - Media Type: {content['media_type']}")
                    logger.info(f"  - Scheduled for: {scheduled_datetime}")
                    logger.info(
                        f"  - Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                    # Parse and compare dates for debugging
                    try:
                        scheduled = datetime.strptime(
                            scheduled_datetime, "%Y-%m-%d %H:%M:%S"
                        )
                        logger.info(
                            f"  - Is scheduled time <= current time? {scheduled <= now}"
                        )
                    except ValueError as e:
                        logger.error(f"  - Error parsing datetime: {e}")
                        logger.error(f"  - Raw date: {content['publish_date']}")
                        logger.error(f"  - Raw time: {content['publish_time']}")

                return pending_content

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_media_content(self, file_id: str) -> Optional[str]:
        """
        Retrieve media content from Google Drive and save to temporary file.

        Args:
            file_id (str): Google Drive file ID

        Returns:
            Optional[str]: Path to temporary file containing the media
        """
        logger.info(f"Attempting to retrieve media content for file_id: {file_id}")
        temp_dir = None
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            temp_file_path = Path(temp_dir) / f"temp_media_{file_id}"
            
            request = self.drive_service.files().get_media(fileId=file_id)
            
            # Get file metadata to determine extension
            file_metadata = self.drive_service.files().get(fileId=file_id, fields='name').execute()
            file_extension = Path(file_metadata['name']).suffix
            temp_file_path = temp_file_path.with_suffix(file_extension)
            
            with open(temp_file_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"Download progress: {int(status.progress() * 100)}%")
            
            logger.info(f"Successfully saved media to temporary file: {temp_file_path}")
            return str(temp_file_path)
            
        except Exception as e:
            logger.error(f"Error retrieving media from Google Drive: {e}")
            if temp_dir:
                shutil.rmtree(temp_dir)
            return None

    def publish_content(self, content: Dict[str, Any]) -> bool:
        """
        Publish a single content item.

        Args:
            content (Dict[str, Any]): Content data from database

        Returns:
            bool: True if published successfully, False otherwise
        """
        temp_files = []  # Keep track of temporary files
        
        try:
            # Validate session before publishing
            if not self.ig_client.validate_session():
                logger.error("❌ Instagram session is invalid. Stopping all publishing attempts.")
                self.update_content_status(content["content_id"], "failed")
                return False  # Return immediately if session is invalid

            # Check for required dependencies for video content
            if content["media_type"] == "video":
                try:
                    import moviepy.editor as mp
                    logger.info("moviepy package is available for video processing")
                except ImportError:
                    logger.error("moviepy package is required for video uploads. Please install: pip install moviepy>=1.0.3")
                    self.update_content_status(content["content_id"], "failed")
                    return False

            logger.warning(
                f"⚠️ INSTAGRAM API ACCESS: Attempting to publish content_id: {content['content_id']}"
            )
            logger.warning("⚠️ Please monitor for automation detection!")

            logger.info(
                f"Starting publication process for content_id: {content['content_id']}"
            )
            logger.info(f"Content type: {content['content_type']}")
            logger.info(f"Media type: {content['media_type']}")

            # Add delay before Instagram API access
            logger.warning("⚠️ Waiting 5 seconds before Instagram API access...")
            time.sleep(5)

            # Prepare location if provided
            location = None
            if content["location_id"]:
                logger.info(f"Setting up location with ID: {content['location_id']}")
                location = Location(
                    pk=content["location_id"], name=content.get("location_name", "")
                )

            # Get media files
            media_paths = content["media_paths"].split(",") if content["media_paths"] else []
            logger.info(f"Found {len(media_paths)} media files to process")

            media_files = []
            for file_id in media_paths:
                logger.info(f"Processing media file ID: {file_id.strip()}")
                temp_file = self.get_media_content(file_id.strip())
                if not temp_file:
                    raise Exception(f"Failed to retrieve media file: {file_id}")
                media_files.append(temp_file)
                temp_files.append(temp_file)
            logger.info(f"Successfully retrieved {len(media_files)} media files")

            # Prepare caption
            caption = content["caption"] or ""
            if content["hashtags"]:
                caption += f"\n\n{content['hashtags']}"
            if content["mentions"]:
                caption += f"\n\n{content['mentions']}"
            logger.info("Caption prepared with hashtags and mentions")

            # Publish based on content type
            result = None
            try:
                if content["content_type"] == "post":
                    if content["media_type"] == "photo":
                        result = self.post_manager.upload_photo(
                            media_files[0], caption=caption, location=location
                        )
                    elif content["media_type"] == "video":
                        result = self.post_manager.upload_video(
                            media_files[0], caption=caption, location=location
                        )
                    elif content["media_type"] in ["photos", "photos and videos"]:
                        result = self.post_manager.upload_album(
                            media_files, caption=caption, location=location
                        )
                elif content["content_type"] == "reel":
                    result = self.post_manager.upload_reel(
                        media_files[0], caption=caption, location=location
                    )
                elif content["content_type"] == "story":
                    # Add story handling here if needed
                    logger.error("Story publishing not yet implemented")
                    return False
            except Exception as e:
                logger.error(f"Publishing error: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

            if result:
                self.update_content_status(content["content_id"], "published", result)
                return True
            else:
                self.update_content_status(content["content_id"], "failed")
                return False

        except Exception as e:
            logger.error(f"Error publishing content {content['content_id']}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.update_content_status(content["content_id"], "failed")
            return False
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if temp_file and os.path.exists(temp_file):
                        os.remove(temp_file)
                        logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Error cleaning up temporary file {temp_file}: {e}")

    def update_content_status(self, content_id: int, status: str, result: Optional[Media] = None) -> None:
        """Update the status of content in both database and Google Sheet."""
        try:
            logger.info(f"Starting status update for content_id {content_id} to {status}")
            
            # First, get the content data including gs_row_number
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM content WHERE content_id = ?",
                    (content_id,)
                )
                content = dict(cursor.fetchone())
                logger.info(f"Retrieved content data: {content}")

                # Update database status
                cursor.execute(
                    "UPDATE content SET status = ? WHERE content_id = ?",
                    (status, content_id),
                )
                logger.info(f"Updated content status in database to: {status}")

                # If published successfully, update corresponding content-specific table
                if status == "published" and result:
                    if isinstance(result, Media):
                        if result.media_type == 1:  # Photo
                            logger.info("Updating posts table for photo content")
                            self._update_posts_table(cursor, content_id, result)
                        elif result.media_type == 2:
                            if result.product_type == "clips":  # Reel
                                logger.info("Updating reels table for reel content")
                                self._update_reels_table(cursor, content_id, result)
                            else:  # Video post
                                logger.info("Updating posts table for video content")
                                self._update_posts_table(cursor, content_id, result)

                conn.commit()
                logger.info("Database updates committed successfully")

            # Update Google Sheet status
            self.update_google_sheet_status(content, status)
            logger.info("Completed status update process")

        except sqlite3.Error as e:
            logger.error(f"Database error updating status: {e}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            logger.error(traceback.format_exc())

    def _update_posts_table(
        self, cursor: sqlite3.Cursor, content_id: int, result: Media
    ) -> None:
        """Update the posts table with the API response data."""
        try:
            cursor.execute(
                """
                INSERT INTO posts (
                    content_id, media_type, product_type, caption, timestamp,
                    media_url, location_pk, location_name, like_count, comment_count,
                    is_album, album_media_ids, album_media_urls, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    result.media_type,
                    result.product_type,
                    result.caption_text,
                    result.taken_at.isoformat(),
                    result.thumbnail_url,
                    result.location.pk if result.location else None,
                    result.location.name if result.location else None,
                    result.like_count,
                    result.comment_count,
                    bool(result.resources),
                    ",".join(str(r.pk) for r in result.resources) if result.resources else None,
                    ",".join(r.thumbnail_url for r in result.resources) if result.resources else None,
                    "active"
                )
            )
            logger.info(f"Successfully updated posts table for content_id: {content_id}")
        except sqlite3.Error as e:
            logger.error(f"Error updating posts table: {e}")
            raise

    def _update_reels_table(
        self, cursor: sqlite3.Cursor, content_id: int, result: Media
    ) -> None:
        """Update the reels table with the API response data."""
        cursor.execute(
            """
            INSERT INTO reels (
                content_id, caption, timestamp, media_url, thumbnail_url,
                location_pk, location_name, like_count, comment_count, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                content_id,  # This is the foreign key referencing content.content_id
                result.caption_text,
                result.taken_at.isoformat(),
                result.video_url,
                result.thumbnail_url,
                result.location.pk if result.location else None,
                result.location.name if result.location else None,
                result.like_count,
                result.comment_count,
                "active",
            ),
        )

    def process_pending_content(self) -> None:
        """Process all pending content that is due for publication."""
        pending_content = self.get_pending_content()
        logger.info(f"Found {len(pending_content)} pending items to publish")

        for content in pending_content:
            try:
                success = self.publish_content(content)
                if success:
                    logger.info(
                        f"Successfully published content {content['content_id']}"
                    )
                else:
                    logger.error(f"Failed to publish content {content['content_id']}")
            except Exception as e:
                logger.error(f"Error processing content {content['content_id']}: {e}")

    def update_google_sheet_status(self, content: Dict[str, Any], status: str) -> None:
        """
        Update the status in Google Sheet for a published/failed content.

        Args:
            content (Dict[str, Any]): The content data including gs_row_number
            status (str): The status to update ('published' or 'failed')
        """
        try:
            if not content.get('gs_row_number'):
                logger.warning(f"No Google Sheet row number for content_id: {content['content_id']}")
                return

            # Get the spreadsheet ID from the GoogleSheetsHandler
            spreadsheet_id = self.gs_handler.spreadsheet_id
            if not spreadsheet_id:
                logger.error("No spreadsheet ID configured")
                return

            # Prepare the update data
            row_number = content['gs_row_number']
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update status column (assuming it's column N)
            status_range = f"'Ig Origin Data'!N{row_number}"
            status_value = [["Y" if status == "published" else "Failed"]]
            
            # Update timestamp column (assuming it's column O)
            timestamp_range = f"'Ig Origin Data'!O{row_number}"
            timestamp_value = [[current_time]]

            # Batch update the sheet
            batch_data = [
                {
                    "range": status_range,
                    "values": status_value
                },
                {
                    "range": timestamp_range,
                    "values": timestamp_value
                }
            ]

            result = self.gs_handler.batch_update(spreadsheet_id, batch_data)
            if result:
                logger.info(f"Updated Google Sheet status for content_id {content['content_id']} to {status}")
            else:
                logger.error(f"Failed to update Google Sheet for content_id {content['content_id']}")

        except Exception as e:
            logger.error(f"Error updating Google Sheet status: {e}")
            logger.error(traceback.format_exc())



