# Module Imports
import mariadb
import sys
# Connect to MariaDB Platform
try:
    conn = mariadb.connect(
        user="admin",
        password="testpassword",
        host="capstone-team-4-dev.cpbxzomz7uyl.us-east-2.rds.amazonaws.com",
        port=3306,
        database="sys"
    )
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

# Get Cursor
cur = conn.cursor()

cur.execute(
    "SELECT * FROM Arrests where Race='W' AND Age=50 AND Gender='F'")

for record in cur:
    print(record)

conn.close()