from typing import Optional, Dict, Any, List
from google_sheets_handler import GoogleSheetsHandler
from datetime import datetime


class FbPostTracker:
    def __init__(self, account_id: str, spreadsheet_id: str):
        self.handler = GoogleSheetsHandler(account_id)
        self.handler.authenticate()
        self.spreadsheet_id = spreadsheet_id

    def get_next_unpublished_post(self) -> Optional[Dict[str, Any]]:
        range_name = "'to publish'!A1:O"  # Extended to column O for media IDs
        values = self.handler.read_spreadsheet(self.spreadsheet_id, range_name)

        if not values or len(values) < 3:
            print("No data found or insufficient rows.")
            return None

        headers = values[1]  # Use the second row as headers

        for row_index, row in enumerate(values[2:], start=3):
            row_dict = dict(zip(headers, row + [""] * (len(headers) - len(row))))
            if row_dict.get("Published? Y/N", "").strip().upper() != "Y":
                row_dict["row_index"] = row_index
                return row_dict

        print("No unpublished posts found.")
        return None

    def mark_post_as_published(
        self, row_index: int, post_result: Dict[str, Any]
    ) -> None:
        range_name = f"'to publish'!L{row_index}:O{row_index}"
        post_id = post_result.get("post_id") or post_result.get("id")
        created_time = post_result.get("created_time") or datetime.now().isoformat()
        media_ids = self.get_media_ids(post_result)
        values = [["Y", created_time, f"'{post_id}", media_ids]]
        self.handler.update_spreadsheet(self.spreadsheet_id, range_name, values)
        print(f"Updated 'to publish' sheet for post ID: {post_id}")

    def add_post_to_published_log(
        self, post_data: Dict[str, Any], post_result: Dict[str, Any]
    ) -> None:
        range_name = "'published'!A:G"  # Changed to include 7 columns (A to G)
        post_id = post_result.get("post_id") or post_result.get("id")
        created_time = post_result.get("created_time") or datetime.now().isoformat()
        media_ids = self.get_media_ids(post_result)
        values = [
            [
                post_data.get("Ref #", ""),  # Column A
                post_data.get("Subject", ""),  # Column B
                post_data.get("Type", ""),  # Column C
                "Y",  # Column D (Published? Y/N)
                created_time,  # Column E (Date and Time)
                f"'{post_id}",  # Column F (ID (str.)) - Prefix with single quote
                media_ids,  # Column G (Media IDs separated by comma)
            ]
        ]
        result = self.handler.append_to_spreadsheet(
            self.spreadsheet_id, range_name, values
        )
        if result:
            print(f"Successfully added post to published log: {post_id}")
        else:
            print(f"Failed to add post to published log: {post_id}")

    def update_post_status(self, row_index: int, status: str) -> None:
        range_name = f"'to publish'!L{row_index}"
        values = [[status]]
        self.handler.update_spreadsheet(self.spreadsheet_id, range_name, values)
        print(f"Updated post status to: {status}")

    def get_media_ids(self, post_result: Dict[str, Any]) -> str:
        media_ids = []
        if 'media_ids' in post_result:
            media_ids = post_result['media_ids']
        elif 'attachments' in post_result:
            for attachment in post_result['attachments'].get('data', []):
                if 'media' in attachment:
                    media_ids.append(attachment['media'].get('id', ''))
        
        return ",".join(f"'{id}" for id in media_ids)
