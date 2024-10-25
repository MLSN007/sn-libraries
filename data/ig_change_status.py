import sqlite3

conn = sqlite3.connect(r"C:\Users\manue\Documents\GitHub007\sn-libraries\data\JK_ig.db")
cursor = conn.cursor()

# Update the 'content' table
cursor.execute("UPDATE content SET status = 'pending' WHERE status = 'failed'")

conn.commit()
conn.close()