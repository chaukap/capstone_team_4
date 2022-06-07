import mariadb
import json

class database_repository:
    def __init__(self) -> None:
        f = open("keys.json")
        keys = json.load(f)

        self.connection = keys["sdp_database"]["host"]
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