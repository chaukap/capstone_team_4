import mariadb
import json

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

    def get_databases(self):
        cur = self.connection.cursor()
        cur.execute("SELECT * FROM ClientDatabases")
        result = [n for n in cur]
        return result
    
    def get_user_databases(self, user_id):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM ClientDatabases WHERE UserId = {str(user_id)}")
        result = [n for n in cur]
        return result

    def get_database_columns(self, database_id):
        cur = self.connection.cursor()
        cur.execute(f"SELECT * FROM ClientDatabaseColumns WHERE DatabaseId = {str(database_id)}")
        result = [n for n in cur]
        return result

    def insert_user(self, email):
        cur = self.connection.cursor()
        cur.execute(f"INSERT INTO Users (Email) VALUES ({email})")
        result = [n for n in cur]
        return result
    
    def insert_database(self, user_id, database_name, 
        host, username, password, table_name, 
        public_name, description):
        cur = self.connection.cursor()
        cur.execute(f"""
            insert into ClientDatabases 
                (DatabaseName, Host, Username, UserPassword, 
                UserId, TableName, PublicName, Description) 
            Values 
                ('{database_name}', '{host}', '{username}', 
                '{password}', {str(user_id)}, '{table_name}', 
                '{public_name}', '{description}')
            """)
        result = [n for n in cur]
        return result

    def insert_database_column(self, database_id, name, max_bound, min_bound):
        cur = self.connection.cursor()
        cur.execute(f"""
            INSERT INTO ClientDatabaseColumns 	
	            (DatabaseId, Name, MaxBound, MinBound)
            VALUES 
	            ({database_id}, '{name}', {max_bound}, {min_bound});
            """)
        result = [n for n in cur]
        return result