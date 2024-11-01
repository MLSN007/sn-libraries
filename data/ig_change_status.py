import sqlite3

conn = sqlite3.connect(r"C:\Users\manue\Documents\GitHub007\sn-libraries\data\JK_ig.db")
cursor = conn.cursor()

# Update the 'content' table and count the number of rows affected
cursor.execute("UPDATE content SET status = 'pending' WHERE status = 'failed'")
rows_affected = cursor.rowcount

# Commit the changes and close the connection
conn.commit()
conn.close()

# Print the number of rows that have been changed from "failed" to "pending"
print(f"Rows changed from 'failed' to 'pending': {rows_affected}")