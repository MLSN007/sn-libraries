"""
Print the contents of all tables in the Instagram database.
"""

import sqlite3
import os

def print_table_data(table_name: str) -> None:
    """
    Print all data from a specified table.

    Args:
        table_name (str): Name of the table to print
    """
    try:
        conn = sqlite3.connect(r"C:\Users\manue\Documents\GitHub007\sn-libraries\data\JK_ig.db")
        cursor = conn.cursor()

        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"\nTable: {table_name}")
        print("|".join(columns))

        # Get and print data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print("  |  ".join(str(item) for item in row))
        else:
            print("No data found in this table.")

        conn.close()

    except sqlite3.Error as e:
        print(f"Error accessing table {table_name}: {e}")

if __name__ == "__main__":
    # List of table names - Add 'reels' to the list
    tables = ["content", "posts", "reels", "stories", "comments"]

    # Print data for each table
    for table in tables:
        print_table_data(table)
