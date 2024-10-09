import datetime
from src.data_handling.google_sheets_handler import GoogleSheetsHandler


class GoogleSheetsRW:
    def __init__(self, account_id, spreadsheet_id):
        self.handler = GoogleSheetsHandler(account_id)
        self.handler.authenticate()
        self.spreadsheet_id = spreadsheet_id

    def read_unpublished_row(self):
        range_name = "'to publish'!A:K"
        values = self.handler.read_spreadsheet(self.spreadsheet_id, range_name)

        if not values:
            print("No data found.")
            return None

        for row_index, row in enumerate(
            values[1:], start=2
        ):  # Start from 2 to account for header row
            if (
                len(row) < 11 or not row[10]
            ):  # Check if "Published? Y/N" column is empty
                return row_index, row

        print("No unpublished rows found.")
        return None

    def write_published_data(self, row_index, published_data):
        range_name = f"'to publish'!L{row_index}:N{row_index}"
        self.handler.write_to_spreadsheet(
            self.spreadsheet_id, range_name, [published_data]
        )

    def write_to_published_tab(self, data):
        range_name = "'published'!A:F"
        self.handler.write_to_spreadsheet(self.spreadsheet_id, range_name, [data])
