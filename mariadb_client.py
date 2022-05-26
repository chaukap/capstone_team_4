# Module Imports
import mariadb
import sys

def get_table_schema(username, password, host, database, table, port=3306):
    try:
        conn = mariadb.connect(
            user=username,
            password=password,
            host = host,
            database=database,
            port=port
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        return

    cur = conn.cursor()
    cur.execute(f"DESCRIBE {table};")

    result = [n for n in cur]

    conn.close()
    return result
