import datetime
from typing import Optional, Tuple, List, Any, Dict
from google_sheets_handler import GoogleSheetsHandler


class GoogleSheetsRW:
    def __init__(self, account_id: str, spreadsheet_id: str):
        self.handler = GoogleSheetsHandler(account_id)
        self.handler.authenticate()
        self.spreadsheet_id = spreadsheet_id

    def read_unpublished_row(self) -> Optional[Tuple[int, Dict[str, Any]]]:
        range_name = "'to publish'!A1:N"  # Extend range to include all columns
        values = self.handler.read_spreadsheet(self.spreadsheet_id, range_name)

        if (
            not values or len(values) < 3
        ):  # Check if we have at least 3 rows (2 header rows + 1 data row)
            print("No data found or insufficient rows.")
            return None

        headers = values[1]  # Use the second row as headers
        print(f"Headers: {headers}")

        for row_index, row in enumerate(
            values[2:], start=3
        ):  # Start from the third row, index 3
            row_dict = dict(zip(headers, row + [""] * (len(headers) - len(row))))
            published_status = row_dict.get("Published? Y/N", "").strip().upper()
            if published_status != "Y":
                return row_index, row_dict

        print("No unpublished rows found.")
        return None

    def write_published_data(
        self, row_index: int, published_data: Dict[str, Any]
    ) -> None:
        range_name = f"'to publish'!L{row_index}:N{row_index}"
        headers = ["Published? Y/N", "Date Published", "Post ID"]
        values = [[published_data.get(header, "") for header in headers]]
        result = self.handler.write_to_spreadsheet(
            self.spreadsheet_id, range_name, values
        )
        if result is None:
            print(f"Failed to write published data to row {row_index}")
        else:
            print(f"Successfully wrote published data to row {row_index}")

    def write_to_published_tab(self, data: Dict[str, Any]) -> None:
        range_name = "'published'!A:F"
        headers = ["Date", "Time", "Type", "Title", "Description", "Link"]
        values = [[data.get(header, "") for header in headers]]
        result = self.handler.write_to_spreadsheet(
            self.spreadsheet_id, range_name, values, insert_data_option="INSERT_ROWS"
        )
        if result is None:
            print("Failed to write data to published tab")
        else:
            print("Successfully wrote data to published tab")
