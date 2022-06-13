import mariadb
import json
from models.user import user
from models.database import database

class database_repository:
    def __init__(self) -> None:
        f = open("keys.json")
        keys = json.load(f)

        try:
            self.connection = mariadb.connect(
                user=keys["sdp_database"]["username"],
                password=keys["sdp_database"]["password"],
                host=keys["sdp_database"]["host"],
                database=keys["sdp_database"]["database"],
                port=keys["sdp_database"]["port"]
            )
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            return

    def __del__(self):
        if self.connection:
            self.connection.close()

    def get_user(self, google_id):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM Users WHERE GoogleId = '{str(google_id)}'")
        result = [n for n in cur]
        if len(result) == 0:
            return None
        cur.close()
        return user(result[0])

    def get_user_by_email(self, email):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM Users WHERE Email = '{email}'")
        result = [n for n in cur]
        if len(result) == 0:
            return None
        return user(result[0])

    def get_database(self, id):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM ClientDatabases WHERE Id = {str(id)}")
        result = [database(n) for n in cur]
        return result[0]

    def get_databases(self):
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM ClientDatabases")
        result = [database(n) for n in cur]
        return result
    
    def get_user_databases(self, user_id):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM ClientDatabases WHERE UserId = {str(user_id)}")
        result = [database(n) for n in cur]
        cur.close()
        return result

    def get_database_columns(self, database_id):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM ClientDatabaseColumns WHERE DatabaseId = {str(database_id)}")
        result = [n for n in cur]
        return result

    def insert_user(self, google_id, email):
        cur = self.connection.cursor()
        query = f"INSERT INTO Users (Email, GoogleId) VALUES ('{email}', '{str(google_id)}')"
        cur.execute(query)
        self.connection.commit()
        return
    
    def insert_database(self, user_id, database_name, 
        host, username, password, table_name, port, 
        public_name, description):
        cur = self.connection.cursor()
        cur.execute(f"""
            insert into ClientDatabases 
                (DatabaseName, Host, Username, UserPassword, 
                UserId, TableName, PublicName, Description, Port) 
            Values 
                ('{database_name}', '{host}', '{username}', 
                '{password}', {str(user_id)}, '{table_name}', 
                '{public_name}', '{description}', {str(port)})
            """)
        self.connection.commit()
        return

    def insert_database_column(self, database_id, name, max_bound, min_bound):
        cur = self.connection.cursor()
        cur.execute(f"""
            INSERT INTO ClientDatabaseColumns 	
	            (DatabaseId, Name, MaxBound, MinBound)
            VALUES 
	            ({database_id}, '{name}', {max_bound}, {min_bound});
            """)
        self.connection.commit()
        return