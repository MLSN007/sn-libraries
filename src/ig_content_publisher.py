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
import json
import random

from ig_client import IgClient
from ig_post_manager import IgPostManager
from ig_utils import IgUtils
from google_sheets_handler import GoogleSheetsHandler
from instagrapi.types import (
    Media,
    Location,
    StoryMention,
    StoryLink,
    StoryHashtag,
    UserShort,
    Hashtag,
)

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

        # Try to authenticate Google services
        try:
            self.gs_handler.authenticate()
            if not self.gs_handler.sheets_service or not self.gs_handler.drive_service:
                raise Exception("Google services authentication failed")
        except Exception as e:
            logger.error(f"Failed to authenticate Google services: {e}")
            logger.info("You may need to re-authenticate or provide new credentials")
            raise

        # Initialize Google Sheet setup
        folder_name = "ig JK tests"  # Make this configurable if needed
        self.folder_id = self.gs_handler.get_folder_id(folder_name)
        if self.folder_id:
            spreadsheet_name = f"{account_id} IG input table"
            self.gs_handler.spreadsheet_id = self.gs_handler.get_file_id_by_name(
                spreadsheet_name, self.folder_id
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
        """Retrieve media content from Google Drive with retry logic."""
        logger.info(f"Attempting to retrieve media content for file_id: {file_id}")
        temp_dir = None
        max_retries = 3
        retry_delay = 5

        # Check if Google services are available
        if not self.gs_handler.drive_service:
            try:
                logger.info("Attempting to re-authenticate Google services...")
                self.gs_handler.authenticate()
                if not self.gs_handler.drive_service:
                    raise Exception("Failed to authenticate Google Drive service")
            except Exception as e:
                logger.error(f"Failed to re-authenticate: {e}")
                return None

        for attempt in range(max_retries):
            try:
                temp_dir = tempfile.mkdtemp()
                temp_file_path = Path(temp_dir) / f"temp_media_{file_id}"

                # Get media content
                request = self.gs_handler.drive_service.get_media(fileId=file_id)

                # Get file metadata
                file_metadata = self.gs_handler.drive_service.get(
                    fileId=file_id, fields="name"
                ).execute()

                # Get file extension
                file_extension = Path(file_metadata["name"]).suffix
                temp_file_path = temp_file_path.with_suffix(file_extension)

                with open(temp_file_path, "wb") as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            logger.info(
                                f"Download progress: {int(status.progress() * 100)}%"
                            )

                logger.info(
                    f"Successfully saved media to temporary file: {temp_file_path}"
                )
                return str(temp_file_path)

            except Exception as e:
                logger.error(
                    f"Error retrieving media from Google Drive (attempt {attempt + 1}/{max_retries}): {e}"
                )
                try:
                    if temp_dir and os.path.exists(temp_dir):
                        # Close any open handles to the file
                        import gc

                        gc.collect()
                        time.sleep(1)  # Give time for handles to be released
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as cleanup_e:
                    logger.warning(f"Error during cleanup: {cleanup_e}")

                if attempt < max_retries - 1:
                    try:
                        logger.info("Attempting to re-authenticate before retry...")
                        self.gs_handler.authenticate()
                    except Exception as auth_e:
                        logger.error(f"Re-authentication failed: {auth_e}")
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    return None

    def publish_content(self, content: Dict[str, Any]) -> bool:
        """
        Publish a single content item.

        Args:
            content (Dict[str, Any]): Content data from database

        Returns:
            bool: True if published successfully, False otherwise
        """
        # First validate all required resources
        try:
            logger.info(f"Validating resources for content_id: {content['content_id']}")
            
            # Check required fields based on content type
            required_fields = ['content_type', 'media_type', 'caption', 'media_paths']
            if content['content_type'] == 'story':
                # Add story-specific required fields
                required_fields.extend(['mentions', 'hashtags'])
            
            missing_fields = [field for field in required_fields 
                             if not content.get(field)]
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                self.update_content_status(content['content_id'], 'failed', 
                                         error=f"Missing required fields: {missing_fields}")
                return False

            # Validate media files first
            media_paths = content["media_paths"].split(",") if content["media_paths"] else []
            if not media_paths:
                logger.error("No media files specified")
                self.update_content_status(content['content_id'], 'failed', 
                                         error="No media files specified")
                return False

            # Try to access each media file without downloading
            for file_id in media_paths:
                file_id = file_id.strip()
                if not self.gs_handler.verify_file_exists(file_id):
                    logger.error(f"Media file not accessible: {file_id}")
                    self.update_content_status(content['content_id'], 'failed',
                                             error=f"Media file not accessible: {file_id}")
                    return False
                logger.info(f"Verified access to media file: {file_id}")

            # Validate location if provided
            if content.get("location_id"):
                try:
                    location = Location(
                        pk=content["location_id"],
                        name=content.get("location_name", "")
                    )
                    logger.info(f"Validated location: {location.name}")
                except Exception as e:
                    logger.error(f"Invalid location data: {e}")
                    self.update_content_status(content['content_id'], 'failed',
                                             error="Invalid location data")
                    return False

            # All validations passed, now proceed with publishing
            logger.info("All resources validated successfully")
            
            # Rest of the publishing code...
            
        except Exception as e:
            logger.error(f"Error validating content {content['content_id']}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.update_content_status(content['content_id'], 'failed',
                                     error=f"Validation error: {str(e)}")
            return False

        temp_files = []  # Keep track of temporary files

        try:
            # Validate session before publishing
            if not self.ig_client.validate_session():
                logger.error(
                    "❌ Instagram session is invalid. Attempting to re-authenticate..."
                )
                try:
                    # Force a new login
                    self.ig_client.client.login(force=True)
                    if not self.ig_client.validate_session():
                        logger.error(
                            "❌ Re-authentication failed. Stopping publishing attempt."
                        )
                        self.update_content_status(content["content_id"], "failed")
                        return False
                    logger.info("✅ Successfully re-authenticated")
                except Exception as e:
                    logger.error(f"❌ Re-authentication error: {e}")
                    self.update_content_status(content["content_id"], "failed")
                    return False

            # Check for required dependencies for video content
            if content["media_type"] == "video":
                try:
                    import moviepy.editor as mp

                    logger.info("moviepy package is available for video processing")
                except ImportError:
                    logger.error(
                        "moviepy package is required for video uploads. Please install: pip install moviepy>=1.0.3"
                    )
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
            logger.warning(" Waiting 5 seconds before Instagram API access...")
            time.sleep(5)

            # Prepare location if provided
            location = None
            if content["location_id"]:
                logger.info(f"Setting up location with ID: {content['location_id']}")
                location = Location(
                    pk=content["location_id"], name=content.get("location_name", "")
                )

            # Get media files
            media_paths = (
                content["media_paths"].split(",") if content["media_paths"] else []
            )
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
                    result = self.publish_story(content)
            except Exception as e:
                logger.error(f"Publishing error: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise

            if result:
                # Update database with the result
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()

                    # Update content status first
                    self.update_content_status(
                        content["content_id"], "published", result
                    )

                    # Try to update specific content table, but don't fail if it errors
                    try:
                        if content["content_type"] == "post":
                            self._update_posts_table(
                                cursor, content["content_id"], result
                            )
                        elif content["content_type"] == "reel":
                            self._update_reels_table(
                                cursor, content["content_id"], result
                            )
                        elif content["content_type"] == "story":
                            self._update_stories_table(
                                cursor, content["content_id"], result
                            )
                    except Exception as e:
                        logger.error(
                            f"Error updating {content['content_type']} table: {e}"
                        )
                        # Don't raise the exception - the content was still published successfully

                    conn.commit()

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
                        # Close any open handles to the file
                        import gc

                        gc.collect()
                        time.sleep(1)  # Give time for handles to be released
                        os.remove(temp_file)
                        logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Error cleaning up temporary file {temp_file}: {e}")
                    try:
                        # Try alternative cleanup method
                        shutil.rmtree(os.path.dirname(temp_file), ignore_errors=True)
                    except Exception as e2:
                        logger.warning(f"Alternative cleanup also failed: {e2}")

    def update_content_status(
        self, 
        content_id: int, 
        status: str, 
        result: Optional[Media] = None,
        error: Optional[str] = None
    ) -> None:
        """Update the status of content in both database and Google Sheet."""
        try:
            logger.info(f"Starting status update for content_id {content_id} to {status}")
            if error:
                logger.info(f"Error message: {error}")

            # First get the content data including gs_row_number
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM content WHERE content_id = ?", (content_id,)
                )
                content = dict(cursor.fetchone())
                logger.info(f"Retrieved content data: {content}")

                # Update database status
                if error:
                    cursor.execute(
                        """UPDATE content 
                           SET status = ?, error_message = ? 
                           WHERE content_id = ?""",
                        (status, error, content_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE content SET status = ? WHERE content_id = ?",
                        (status, content_id)
                    )
                conn.commit()
                logger.info(f"Updated content status in database to: {status}")

            # Update Google Sheet if we have row number
            if content.get("gs_row_number"):
                # First, get the header row to find column indices
                header_range = "'Ig Origin Data'!1:1"
                headers = self.gs_handler.read_spreadsheet(
                    self.gs_handler.spreadsheet_id, header_range
                )
                if not headers or not headers[0]:
                    logger.error("Failed to read Google Sheet headers")
                    return

                # Create a mapping of column titles to their indices
                column_mapping = {
                    title: idx + 1 for idx, title in enumerate(headers[0])
                }

                # Prepare batch updates
                batch_data = []
                row_number = content["gs_row_number"]

                # Map of fields to update based on status
                updates_map = {
                    "status": status,
                    "error_message": error if error else "",
                }

                if status == "published":
                    current_time = datetime.now()
                    updates_map.update({
                        "publish_date": current_time.strftime("%Y-%m-%d"),
                        "publish_time": current_time.strftime("%H:%M:%S"),
                    })

                # Create batch update data
                for column_title, value in updates_map.items():
                    if column_title in column_mapping:
                        column_letter = self._number_to_column_letter(
                            column_mapping[column_title]
                        )
                        batch_data.append(
                            {
                                "range": f"'Ig Origin Data'!{column_letter}{row_number}",
                                "values": [[value]],
                            }
                        )
                    else:
                        logger.warning(
                            f"Column '{column_title}' not found in Google Sheet"
                        )

                if batch_data:
                    if self.gs_handler.batch_update(
                        self.gs_handler.spreadsheet_id, batch_data
                    ):
                        logger.info(
                            f"Successfully updated Google Sheet for content_id {content_id}"
                        )
                    else:
                        logger.error(
                            f"Failed to update Google Sheet for content_id {content_id}"
                        )
                else:
                    logger.error("No columns to update in Google Sheet")

        except Exception as e:
            logger.error(f"Error updating status: {e}")
            logger.error(traceback.format_exc())

    def _update_posts_table(
        self, cursor: sqlite3.Cursor, content_id: int, result: Media
    ) -> None:
        """Update the posts table with the API response data."""
        try:
            cursor.execute(
                "SELECT post_id FROM posts WHERE content_id = ?", (content_id,)
            )
            existing = cursor.fetchone()

            def safe_get_attr(obj, *attrs, default=None):
                """Try multiple attribute names, return first found or default."""
                for attr in attrs:
                    value = getattr(obj, attr, None)
                    if value is not None:
                        # Convert Pydantic URLs to strings
                        if hasattr(value, "__class__") and value.__class__.__name__ in [
                            "Url",
                            "AnyUrl",
                        ]:
                            return str(value)
                        return value
                return default

            # Get timestamp
            taken_at = safe_get_attr(result, "taken_at", "created_at", "timestamp")
            if taken_at:
                timestamp = (
                    taken_at.isoformat()
                    if hasattr(taken_at, "isoformat")
                    else str(taken_at)
                )
            else:
                timestamp = datetime.now().isoformat()

            # Get media URL and ensure it's a string
            media_url = str(
                safe_get_attr(result, "thumbnail_url", "url", "media_url", default="")
            )
            if hasattr(media_url, "__class__") and media_url.__class__.__name__ in [
                "Url",
                "AnyUrl",
            ]:
                media_url = str(media_url)

            # Get location info
            location = safe_get_attr(result, "location")
            location_pk = location.pk if location else None
            location_name = location.name if location else None

            # Get resources (for album posts)
            resources = safe_get_attr(result, "resources", "carousel_media", default=[])

            # Common values for insert/update
            values = (
                safe_get_attr(result, "media_type", default=1),
                safe_get_attr(result, "product_type", default=""),
                safe_get_attr(result, "caption_text", "caption", default=""),
                timestamp,
                media_url,  # Now guaranteed to be a string
                location_pk,
                location_name,
                safe_get_attr(result, "like_count", default=0),
                safe_get_attr(result, "comment_count", default=0),
                bool(resources),
                (
                    ",".join(
                        str(safe_get_attr(r, "pk", "id", default="")) for r in resources
                    )
                    if resources
                    else None
                ),
                (
                    ",".join(
                        str(safe_get_attr(r, "thumbnail_url", "url", default=""))
                        for r in resources
                    )
                    if resources
                    else None
                ),
                "active",
                content_id,
            )

            try:
                if existing:
                    logger.info(
                        f"Updating existing post record for content_id: {content_id}"
                    )
                    cursor.execute(
                        """
                        UPDATE posts SET
                            media_type = ?, product_type = ?, caption = ?, timestamp = ?,
                            media_url = ?, location_pk = ?, location_name = ?, like_count = ?,
                            comment_count = ?, is_album = ?, album_media_ids = ?,
                            album_media_urls = ?, status = ?
                        WHERE content_id = ?
                        """,
                        values,
                    )
                else:
                    logger.info(
                        f"Inserting new post record for content_id: {content_id}"
                    )
                    cursor.execute(
                        """
                        INSERT INTO posts (
                            media_type, product_type, caption, timestamp,
                            media_url, location_pk, location_name, like_count, comment_count,
                            is_album, album_media_ids, album_media_urls, status, content_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        values,
                    )

                # Verify the update/insert
                cursor.execute(
                    "SELECT * FROM posts WHERE content_id = ?", (content_id,)
                )
                if cursor.fetchone():
                    logger.info(
                        f"Successfully updated posts table for content_id: {content_id}"
                    )
                else:
                    raise Exception("Failed to verify post record after update/insert")

            except sqlite3.Error as e:
                logger.error(f"Database error while updating posts table: {e}")
                logger.error(f"Values being inserted: {values}")
                raise

        except Exception as e:
            logger.error(f"Error updating posts table: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Log error but don't raise - allow the main process to continue

    def _update_reels_table(
        self, cursor: sqlite3.Cursor, content_id: int, result: Media
    ) -> None:
        """
        Update the reels table with the API response data.

        Args:
            cursor (sqlite3.Cursor): Database cursor
            content_id (int): Content ID from the content table
            result (Media): Instagram API response object from reel upload
        """
        try:
            cursor.execute(
                "SELECT reel_id FROM reels WHERE content_id = ?", (content_id,)
            )
            existing = cursor.fetchone()

            def safe_get_attr(obj, *attrs, default=None):
                """Try multiple attribute names, return first found or default."""
                for attr in attrs:
                    value = getattr(obj, attr, None)
                    if value is not None:
                        return value
                return default

            # Get timestamp - Instagrapi uses taken_at
            taken_at = safe_get_attr(result, "taken_at")
            timestamp = taken_at.isoformat() if taken_at else datetime.now().isoformat()

            # Get location info - Instagrapi uses location object
            location = safe_get_attr(result, "location")

            # Get media URLs - Instagrapi provides video_url for reels
            media_url = safe_get_attr(result, "video_url")
            thumbnail_url = safe_get_attr(result, "thumbnail_url")

            # Get audio info - Instagrapi provides music_info for reels
            music_info = safe_get_attr(result, "music_info", "audio_metadata")
            audio_track = json.dumps(music_info) if music_info else ""

            # Get clips metadata - Instagrapi provides clips_metadata
            clips_metadata = safe_get_attr(result, "clips_metadata")
            effects = json.dumps(clips_metadata) if clips_metadata else ""

            # Get duration - Instagrapi provides video_duration
            duration = safe_get_attr(result, "video_duration", default=0)

            values = (
                safe_get_attr(result, "caption_text", "caption", default=""),
                timestamp,
                media_url,
                thumbnail_url,
                location.pk if location else None,
                location.name if location else None,
                safe_get_attr(result, "like_count", default=0),
                safe_get_attr(result, "comment_count", default=0),
                audio_track,
                effects,
                duration,
                "active",
                content_id,
            )

            if existing:
                logger.info(
                    f"Updating existing reel record for content_id: {content_id}"
                )
                cursor.execute(
                    """
                    UPDATE reels SET
                        caption = ?, timestamp = ?, media_url = ?, thumbnail_url = ?,
                        location_pk = ?, location_name = ?, like_count = ?,
                        comment_count = ?, audio_track = ?, effects = ?, duration = ?,
                        status = ?
                    WHERE content_id = ?
                    """,
                    values,
                )
            else:
                logger.info(f"Inserting new reel record for content_id: {content_id}")
                cursor.execute(
                    """
                    INSERT INTO reels (
                        caption, timestamp, media_url, thumbnail_url,
                        location_pk, location_name, like_count, comment_count,
                        audio_track, effects, duration, status, content_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )

            # Verify the update/insert
            cursor.execute("SELECT * FROM reels WHERE content_id = ?", (content_id,))
            if cursor.fetchone():
                logger.info(
                    f"Successfully updated reels table for content_id: {content_id}"
                )
            else:
                raise Exception("Failed to verify reel record after update/insert")

        except Exception as e:
            logger.error(f"Error updating reels table: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Log error but don't raise - allow the main process to continue

    def _update_stories_table(
        self, cursor: sqlite3.Cursor, content_id: int, result: Media
    ) -> None:
        """
        Update the stories table with the API response data.

        Args:
            cursor (sqlite3.Cursor): Database cursor
            content_id (int): Content ID from the content table
            result (Media): Instagram API response object from story upload
        """
        try:

            def safe_get_attr(obj, *attrs, default=None):
                """Try multiple attribute names, return first found or default."""
                for attr in attrs:
                    value = getattr(obj, attr, None)
                    if value is not None:
                        return value
                return default

            # Get mentions
            mentions = safe_get_attr(result, "mentions", default=[])
            mention_usernames = (
                ",".join(mention.user.username for mention in mentions)
                if mentions
                else None
            )

            # Get hashtags
            hashtags = safe_get_attr(result, "hashtags", default=[])
            hashtag_names = (
                ",".join(f"#{tag.name}" for tag in hashtags) if hashtags else None
            )

            # Get story link
            story_cta = safe_get_attr(result, "story_cta", default=[])
            link = story_cta[0].url if story_cta else None

            # Get media URL based on type
            media_type = safe_get_attr(result, "media_type", default=1)
            media_url = (
                safe_get_attr(result, "video_url")
                if media_type == 2
                else safe_get_attr(result, "thumbnail_url")
            )

            cursor.execute(
                """
                INSERT INTO stories (
                    story_id, content_id, code, taken_at, reel_url,
                    caption, mentions, location_id, hashtags, link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(safe_get_attr(result, "pk", "id")),
                    content_id,
                    safe_get_attr(result, "code"),
                    safe_get_attr(result, "taken_at").isoformat(),
                    media_url,
                    safe_get_attr(result, "caption_text", "caption", default=""),
                    mention_usernames,
                    (
                        safe_get_attr(result, "location.pk")
                        if safe_get_attr(result, "location")
                        else None
                    ),
                    hashtag_names,
                    link,
                ),
            )
            logger.info(
                f"Successfully updated stories table for content_id: {content_id}"
            )

        except Exception as e:
            logger.error(f"Error updating stories table: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Log error but don't raise - allow the main process to continue

    def publish_story(self, content: Dict[str, Any]) -> Optional[Media]:
        """
        Publish a story to Instagram using Instagrapi v2.1.2.

        Args:
            content (Dict[str, Any]): Content data from database

        Returns:
            Optional[Media]: Published story media object if successful, None otherwise
        """
        temp_file = None
        try:
            # Get media file
            media_paths = (
                content["media_paths"].split(",") if content["media_paths"] else []
            )
            if not media_paths:
                raise ValueError("No media file provided for story")

            temp_file = self.get_media_content(media_paths[0].strip())
            if not temp_file:
                raise ValueError(f"Failed to retrieve media file")

            # Prepare mentions
            story_mentions = []
            if content["mentions"]:
                for mention in content["mentions"].split():
                    username = mention.strip("@")
                    try:
                        user_info = self.ig_client.client.user_info_by_username(
                            username
                        )
                        if user_info:
                            user_short = UserShort(
                                pk=user_info.pk,
                                username=user_info.username,
                                full_name=user_info.full_name,
                            )
                            story_mentions.append(
                                StoryMention(
                                    user=user_short, x=0.5, y=0.5, width=0.5, height=0.1
                                )
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to process mention for user {username}: {e}"
                        )

            # Prepare hashtags
            story_hashtags = []
            if content["hashtags"]:
                for idx, tag in enumerate(content["hashtags"].split()):
                    try:
                        clean_tag = tag.strip("#")
                        hashtag_info = self.ig_client.client.hashtag_info(clean_tag)
                        if hashtag_info:
                            hashtag = Hashtag(
                                name=clean_tag,
                                id=hashtag_info.id,
                                media_count=hashtag_info.media_count,
                            )
                            story_hashtags.append(
                                StoryHashtag(
                                    hashtag=hashtag,
                                    x=0.5,
                                    y=0.3 + (idx * 0.1),
                                    width=0.5,
                                    height=0.1,
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Failed to process hashtag {clean_tag}: {e}")

            # Prepare links
            story_links = []
            if content.get("link"):
                try:
                    story_links.append(StoryLink(webUri=content["link"]))
                except Exception as e:
                    logger.warning(f"Failed to process link: {e}")

            # Add delay before API call
            logger.info("Waiting 2 seconds before story upload...")
            time.sleep(2)

            # Prepare upload parameters
            upload_kwargs = {"path": temp_file, "caption": content.get("caption", "")}

            # Only add optional parameters if they exist
            if story_mentions:
                upload_kwargs["mentions"] = story_mentions
            if story_hashtags:
                upload_kwargs["hashtags"] = story_hashtags
            if story_links:
                upload_kwargs["links"] = story_links

            # Publish story based on media type
            if content["media_type"] == "photo":
                result = self.post_manager.client.photo_upload_to_story(**upload_kwargs)
            elif content["media_type"] == "video":
                result = self.post_manager.client.video_upload_to_story(**upload_kwargs)
            else:
                raise ValueError(
                    f"Unsupported media type for story: {content['media_type']}"
                )

            if result:
                logger.info(f"Successfully published story. Story ID: {result.pk}")

                # Update stories table in database
                try:
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()

                        # Insert story data into stories table
                        cursor.execute(
                            """
                            INSERT INTO stories (
                                story_id, content_id, code, taken_at, reel_url,
                                caption, mentions, location_id, hashtags, link
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                str(result.pk),
                                content["content_id"],
                                result.code,
                                result.taken_at.isoformat(),
                                (
                                    result.video_url
                                    if content["media_type"] == "video"
                                    else result.thumbnail_url
                                ),
                                content.get("caption", ""),
                                content.get("mentions", ""),
                                content.get("location_id"),
                                content.get("hashtags", ""),
                                content.get("link"),
                            ),
                        )

                        # Update content status to published
                        cursor.execute(
                            """
                            UPDATE content 
                            SET status = 'published' 
                            WHERE content_id = ?
                        """,
                            (content["content_id"],),
                        )

                        conn.commit()
                        logger.info(
                            f"Successfully updated stories table for content_id: {content['content_id']}"
                        )

                except sqlite3.Error as e:
                    logger.error(f"Database error while updating stories table: {e}")
                    logger.error(traceback.format_exc())
                    raise
                except Exception as e:
                    logger.error(f"Error publishing story: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return None
                finally:
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                            logger.info(f"Cleaned up temporary file: {temp_file}")
                        except Exception as e:
                            logger.warning(
                                f"Error cleaning up temporary file {temp_file}: {e}"
                            )
                    return result
        except Exception as e:
            logger.error(f"Error publishing story: {e}")
            return None
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Error cleaning up temporary file {temp_file}: {e}")
            return result

    def verify_instagram_health(self) -> bool:
        """
        Verify Instagram session health and check for potential IP/automation flags.

        Returns:
            bool: True if everything is healthy, False otherwise
        """
        try:
            logger.info("Verifying Instagram session and IP health...")

            # Check if session is valid
            if not self.ig_client.validate_session():
                logger.error("❌ Instagram session is invalid")
                return False

            # Check for IP-related issues by attempting some safe operations
            try:
                # Try to fetch own profile - should be fast and safe
                user_id = self.ig_client.client.user_id
                user_info = self.ig_client.client.user_info(user_id)
                if not user_info:
                    raise Exception("Failed to fetch user info")

                # Try to fetch user feed - good indicator of IP status
                user_medias = self.ig_client.client.user_medias(user_id, amount=1)
                if user_medias is None:
                    raise Exception("Failed to fetch user medias")

                # Try to fetch story feed - another good health indicator
                reels = self.ig_client.client.user_stories(user_id)
                if reels is None:
                    raise Exception("Failed to fetch user stories")

                logger.info("✅ IP checks passed successfully")
                return True

            except Exception as e:
                error_message = str(e).lower()

                # Check for common IP/automation detection indicators
                if "feedback_required" in error_message:
                    logger.error("❌ Instagram has flagged potential automation")
                    return False
                elif "challenge_required" in error_message:
                    logger.error("❌ Instagram requires verification challenge")
                    return False
                elif "login_required" in error_message:
                    logger.error("❌ Session has expired")
                    return False
                elif "rate_limit" in error_message:
                    logger.error("❌ Rate limit hit - IP may be flagged")
                    return False
                else:
                    logger.error(f"❌ Instagram API error: {e}")
                    return False

        except Exception as e:
            logger.error(f"Error verifying Instagram health: {e}")
            return False

    def process_pending_content(self) -> None:
        """Process all pending content that is due for publication."""
        # First verify Instagram health
        if not self.verify_instagram_health():
            logger.error("Instagram health check failed. Stopping process.")
            return

        pending_content = self.get_pending_content()
        logger.info(f"Found {len(pending_content)} pending items to publish")

        # If no pending content, return immediately
        if not pending_content:
            logger.info("No pending content to process")
            return

        for i, content in enumerate(pending_content):
            try:
                logger.info(f"\nProcessing content {i+1} of {len(pending_content)}")

                # Re-verify Instagram health before each post
                if not self.verify_instagram_health():
                    logger.error("Instagram health check failed. Stopping process.")
                    return

                # Add random delay between posts (2-5 minutes)
                if i > 0:  # Don't delay before first post
                    delay = random.uniform(120, 300)
                    logger.info(f"Adding random delay of {delay:.1f} seconds...")
                    time.sleep(delay)

                success = self.publish_content(content)

                if success:
                    logger.info(
                        f"Successfully published content {content['content_id']}"
                    )
                else:
                    logger.error(f"Failed to publish content {content['content_id']}")

            except Exception as e:
                logger.error(f"Error processing content {content['content_id']}: {e}")

            finally:
                # Only ask to continue if there are more items
                if i < len(pending_content) - 1:
                    continue_response = input(
                        "\nDo you want to process the next content? (y/N/q): "
                    ).lower()
                    if continue_response == "q":
                        logger.info("Exiting program...")
                        return
                    elif continue_response != "y":
                        logger.info("Stopping content processing")
                        return

    def update_google_sheet_status(self, content: Dict[str, Any], status: str) -> None:
        """Update the status in Google Sheet for a published/failed content."""
        try:
            if not content.get("gs_row_number"):
                logger.warning(
                    "No Google Sheet row number for content_id: %s",
                    content["content_id"],
                )
                return

            # Get headers to find correct columns
            headers = self.gs_handler.read_spreadsheet(
                self.gs_handler.spreadsheet_id, "'Ig Origin Data'!1:1"
            )[0]

            # Find required column indices
            try:
                status_col = self._number_to_column_letter(headers.index("status") + 1)
                timestamp_col = self._number_to_column_letter(
                    headers.index("publish_timestamp") + 1
                )
            except ValueError as e:
                logger.error("Required column not found in header: %s", str(e))
                return

            row_number = content["gs_row_number"]
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Prepare batch update
            batch_data = [
                {
                    "range": f"'Ig Origin Data'!{status_col}{row_number}",
                    "values": [["Y" if status == "published" else "Failed"]],
                },
                {
                    "range": f"'Ig Origin Data'!{timestamp_col}{row_number}",
                    "values": [[current_time]],
                },
            ]

            result = self.gs_handler.batch_update(
                self.gs_handler.spreadsheet_id, batch_data
            )
            if result:
                logger.info(
                    "Updated Google Sheet status for content_id %s to %s",
                    content["content_id"],
                    status,
                )
            else:
                logger.error(
                    "Failed to update Google Sheet for content_id %s",
                    content["content_id"],
                )

        except Exception as e:
            logger.error("Error updating Google Sheet status: %s", str(e))

    def _number_to_column_letter(self, n: int) -> str:
        """Convert a column number to Excel-style column letter (A, B, C, ... Z, AA, AB, etc.)."""
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string

    def _check_rate_limits(self) -> bool:
        """Check if we're approaching Instagram's rate limits."""
        try:
            # Get the user's recent actions count
            user_id = self.ig_client.client.user_id
            user_feed = self.ig_client.client.user_feed(user_id)

            # Count recent posts (last 24 hours)
            recent_posts = 0
            now = datetime.now()
            for post in user_feed:
                if (now - post.taken_at).total_seconds() < 86400:  # 24 hours in seconds
                    recent_posts += 1

            # Instagram's typical limits:
            # - Max 25-30 posts per 24 hours
            # - Max 100 actions per hour
            if recent_posts >= 25:
                logger.warning("⚠️ Approaching Instagram's daily post limit")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking rate limits: {e}")
            return False

    def _add_safe_delay(self) -> None:
        """Add a randomized delay to avoid automation detection."""
        base_delay = random.uniform(30, 60)  # Base delay between 30-60 seconds

        # Add extra delay based on time of day (more during night)
        hour = datetime.now().hour
        if 0 <= hour < 6:  # Night time
            extra_delay = random.uniform(60, 120)
        else:
            extra_delay = random.uniform(15, 45)

        total_delay = base_delay + extra_delay
        logger.info(f"Adding safety delay of {total_delay:.1f} seconds...")
        time.sleep(total_delay)

    def cleanup(self) -> None:
        """Clean up resources before shutdown."""
        # Add any cleanup logic here
        logger.info("Cleaning up resources...")
