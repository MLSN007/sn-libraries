import sys
import os
from typing import Optional, Tuple, List, Any, Dict
import datetime

from google_sheets_rw import GoogleSheetsRW


def process_row(row_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process the row data and prepare it for writing back to the spreadsheet.

    Args:
        row_data (Dict[str, Any]): The data from the unpublished row.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: A tuple containing the published data and the data for the published tab.
    """
    current_datetime = datetime.datetime.now()
    published_data = {
        "Published? Y/N": "Y",
        "Date and Time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        "ID (str.)": "PLACEHOLDER_ID",
    }
    published_tab_data = {
        "Date": current_datetime.strftime("%Y-%m-%d"),
        "Time": current_datetime.strftime("%H:%M:%S"),
        "Type": row_data.get("Type", ""),
        "Title": row_data.get("Subject", ""),
        "Description": row_data.get("Post comment", ""),
        "Link": row_data.get("Media Souce links separated by comma", ""),
    }
    return published_data, published_tab_data


def main():
    account_id = "JK"
    spreadsheet_id = "1wrvG3wmptA76kywbVe1gy5as-ALDzmebLvqoxWIw9mw"

    try:
        gs_rw = GoogleSheetsRW(account_id, spreadsheet_id)
    except ValueError as e:
        print(f"Error initializing GoogleSheetsRW: {e}")
        return

    result = gs_rw.read_unpublished_row()
    if result is None:
        print("No unpublished rows to process.")
        return

    row_index, row_data = result

    print(f"\nProcessing row {row_index}:")
    print("-" * 40)
    for key, value in row_data.items():
        print(f"{key}: {value}")
    print("-" * 40)

    published_data, published_tab_data = process_row(row_data)

    gs_rw.write_published_data(row_index, published_data)
    gs_rw.write_to_published_tab(published_tab_data)

    print("Processing completed successfully.")


if __name__ == "__main__":
    main()
