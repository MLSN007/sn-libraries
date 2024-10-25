import sqlite3

def print_table_data(table_name):
    """
    Reads all data from the specified table and prints it in a formatted way.
    """
    # -------------------------------------------------------------------------
    conn = sqlite3.connect(
        r"C:\Users\manue\Documents\GitHub007\sn-libraries\data\JK_ig.db"
    )  # Replace with your database name
    # -------------------------------------------------------------------------
    cursor = conn.cursor()

    try:
        # Execute a SELECT query to fetch all rows from the table
        cursor.execute(f'SELECT * FROM {table_name}')

        # Fetch all results
        rows = cursor.fetchall()

        # Print the table name
        print(f"\nTable: {table_name}")

        # If there are no rows, print a message
        if not rows:
            print("No data found in this table.")
            return

        # Get the column names
        column_names = [description[0] for description in cursor.description]
        print("|".join(column_names))  # Print column names as headers

        # Print the data rows
        for row in rows:
            print("  |  ".join(str(value) for value in row))
            print("\n")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    # List of table names
    tables = ["content", "posts", "stories", "comments"]

    # Print data for each table
    for table in tables:
        print_table_data(table)