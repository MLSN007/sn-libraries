from google_sheets_rw import GoogleSheetsRW
import datetime


def main():
    # Initialize GoogleSheetsRW with your account ID and spreadsheet ID
    account_id = "JK"  # Replace with your actual account ID
    spreadsheet_id = "1wrvG3wmptA76kywbVe1gy5as-ALDzmebLvqoxWIw9mw"  # Replace with your actual spreadsheet ID
    gs_rw = GoogleSheetsRW(account_id, spreadsheet_id)

    # Read the first unpublished row
    result = gs_rw.read_unpublished_row()
    if result is None:
        print("No unpublished rows to process.")
        return

    row_index, row_data = result

    # Print the content of each cell
    for i, cell in enumerate(row_data):
        print(f"Column {chr(65+i)}: {cell}")

    # Here you would normally process the data
    # For now, we'll just use placeholder data

    # Generate published data
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    placeholder_id = "PLACEHOLDER_ID"
    published_data = ["Y", current_datetime, placeholder_id]

    # Write published data to the original sheet
    gs_rw.write_published_data(row_index, published_data)

    # Prepare data for the "published" tab (6 columns)
    published_tab_data = row_data[:6]

    # Write to the "published" tab
    gs_rw.write_to_published_tab(published_tab_data)

    print("Processing completed successfully.")


if __name__ == "__main__":
    main()
