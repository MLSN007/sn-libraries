from typing import Optional, Dict, Any, List
from google_sheets_handler import GoogleSheetsHandler
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class FbPostTracker:
    def __init__(self, account_id: str, spreadsheet_id: str):
        self.handler = GoogleSheetsHandler(account_id)
        self.handler.authenticate()
        self.spreadsheet_id = spreadsheet_id

    def get_next_post(self) -> Optional[Dict[str, Any]]:
        """Retrieve the next unpublished post from the spreadsheet."""
        range_name = "'to publish'!A1:P"  # Extended to column P to include all columns
        values = self.handler.read_spreadsheet(self.spreadsheet_id, range_name)

        if (
            not values or len(values) < 3
        ):  # We need at least 3 rows: 2 header rows + 1 data row
            print("No data found or insufficient rows.")
            return None

        headers = values[1]  # Use the second row as headers
        print(f"Headers: {headers}")  # Debug print

        for row_index, row in enumerate(
            values[2:], start=3
        ):  # Start from the third row, index 3
            row_dict = dict(zip(headers, row + [""] * (len(headers) - len(row))))
            published_status = row_dict.get("Published? Y/N", "").strip().upper()
            post_type = row_dict.get("Type", "").strip()
            print(
                f"Row {row_index}: Published status: {published_status}, Type: {post_type}"
            )  # Debug print
            if published_status != "Y":
                row_dict["row_index"] = row_index
                print(f"Returning post data: {row_dict}")  # Debug print
                return row_dict

        print("No unpublished posts found.")
        return None

    def mark_post_as_published(
        self, row_index: int, post_result: Dict[str, Any]
    ) -> None:
        """Update the published status and related information in the spreadsheet."""
        try:
            # Get headers to find correct columns
            headers = self.handler.read_spreadsheet(
                self.spreadsheet_id, "'to publish'!1:1"
            )[0]

            # Map column names to indices
            col_mapping = {
                "Published? Y/N": None,
                "Date and Time": None,
                "Post ID": None,
                "Media IDs": None,
                "Post Link": None,
                "Media Links": None,
            }

            for idx, header in enumerate(headers):
                if header in col_mapping:
                    col_mapping[header] = self._number_to_column_letter(idx + 1)

            # Construct range using found columns
            start_col = min(col for col in col_mapping.values() if col is not None)
            end_col = max(col for col in col_mapping.values() if col is not None)
            range_name = f"'to publish'!{start_col}{row_index}:{end_col}{row_index}"

            # Prepare values in correct order
            values = [
                [
                    "Y",  # Published status
                    datetime.now().isoformat(),  # Timestamp
                    f"'{post_result.get('id', '')}",  # Post ID
                    ",".join(
                        f"'{mid}" for mid in post_result.get("media_ids", [])
                    ),  # Media IDs
                    post_result.get("link", ""),  # Post Link
                    post_result.get("media_links", ""),  # Media Links
                ]
            ]

            result = self.handler.update_spreadsheet(
                self.spreadsheet_id, range_name, values
            )
            if result:
                logger.info(
                    "Successfully updated 'to publish' sheet for post ID: %s",
                    post_result.get("id", ""),
                )
            else:
                logger.error(
                    "Failed to update 'to publish' sheet for post ID: %s",
                    post_result.get("id", ""),
                )

        except Exception as e:
            logger.error("Error updating published status: %s", str(e))

    def add_post_to_published_log(
        self, post_data: Dict[str, Any], post_result: Dict[str, Any]
    ) -> None:
        range_name = "'published'!A:H"
        post_id = post_result.get("id", "")
        created_time = datetime.now().isoformat()
        media_ids = ",".join(f"'{mid}" for mid in post_result.get("media_ids", []))
        post_link = post_result.get("link", "")
        media_links = post_result.get("media_links", "")
        values = [
            [
                post_data.get("Ref #", ""),
                post_data.get("Subject", ""),
                post_data.get("Type", ""),
                "Y",
                created_time,
                f"'{post_id}",
                post_link,
                media_links,
            ]
        ]

        logger.info(f"Adding post to published log. Post ID: {post_id}")
        logger.info(f"Post link: {post_link}")
        logger.info(f"Media links: {media_links}")

        result = self.handler.append_to_spreadsheet(
            self.spreadsheet_id, range_name, values
        )
        if result:
            logger.info(f"Successfully added post to published log: {post_id}")
        else:
            logger.error(f"Failed to add post to published log: {post_id}")

    def update_post_status(
        self, row_index: int, status: str, post_id: str = "", media_ids: str = ""
    ) -> None:
        """Update the status of a post in the spreadsheet."""
        range_name = f"'to publish'!L{row_index}:P{row_index}"
        current_datetime = self.handler.get_current_datetime()
        values = [
            [status, current_datetime, post_id, media_ids, ""]
        ]  # Last empty string for "Post link" column
        self.handler.update_spreadsheet(self.spreadsheet_id, range_name, values)
        print(f"Updated post status to: {status}")

    def get_media_ids(self, post_result: Dict[str, Any]) -> str:
        media_ids = post_result.get("media_ids", [])
        return ",".join(f"'{media_id}" for media_id in media_ids)
