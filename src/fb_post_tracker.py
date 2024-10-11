from typing import Optional, Dict, Any
from google_sheets_handler import GoogleSheetsHandler


class FbPostTracker:
    def __init__(self, account_id: str, spreadsheet_id: str):
        self.handler = GoogleSheetsHandler(account_id)
        self.handler.authenticate()
        self.spreadsheet_id = spreadsheet_id

    def get_next_unpublished_post(self) -> Optional[Dict[str, Any]]:
        range_name = "'to publish'!A1:N"
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

    def mark_post_as_published(self, row_index: int, post_id: str) -> None:
        range_name = f"'to publish'!L{row_index}:N{row_index}"
        values = [["Y", self.handler.get_current_datetime(), post_id]]
        self.handler.write_to_spreadsheet(self.spreadsheet_id, range_name, values)

    def add_post_to_published_log(self, post_data: Dict[str, Any]) -> None:
        range_name = "'published'!A:F"
        values = [
            [
                post_data.get("#", ""),
                post_data.get("Subject", ""),
                post_data.get("Type", ""),
                "Y",
                self.handler.get_current_datetime(),
                post_data.get("ID (str.)", ""),
            ]
        ]
        self.handler.append_to_spreadsheet(self.spreadsheet_id, range_name, values)

    def update_post_status(self, row_index: int, status: str) -> None:
        range_name = f"'to publish'!L{row_index}"
        values = [[status]]
        self.handler.write_to_spreadsheet(self.spreadsheet_id, range_name, values)
