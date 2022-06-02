# Module Imports
import mariadb

class mariadb_client:
    def __init__(self, username, password, host, database, port=3306):
        self.username = username
        self.password = password
        self.host = host
        self.database = database
        self.port = port
        pass

    def execute_query(self, query):
        try:
            conn = mariadb.connect(
                user=self.username,
                password=self.password,
                host=self.host,
                database=self.database,
                port=self.port
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return

        cur = conn.cursor()
        cur.execute(query)
        result = [n for n in cur]

        conn.close()
        return result

    def get_table_schema(self, table):
        try:
            conn = mariadb.connect(
                user=self.username,
                password=self.password,
                host=self.host,
                database=self.database,
                port=self.port
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return

        cur = conn.cursor()
        cur.execute(f"DESCRIBE {table};")
        result = [n for n in cur]

        conn.close()
        return result

    def select_all(self, username, password, host, database, table, port=3306):
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
        cur.execute(f"SELECT * FROM {table};")

        result = [n for n in cur]

        conn.close()
        return result