from query_generator import query_generator
from mariadb_client import mariadb_client
import numpy as np
import pandas as pd

class differential_privacy_engine:
    def __init__(self, username, password, host, database, port=3306):
        self.client = mariadb_client(
            username, password, host, database, port)
        return

    def count(self, table, identifier_column, grouping_column, count_column, epsilon):
        sql_query = query_generator.generate_count_query(
            table, identifier_column, grouping_column, count_column)
        result = pd.DataFrame(
            self.client.execute_query(sql_query["query"])
        )
        result.columns = [grouping_column, count_column, "count"]
        result["count"] = result.apply(
            lambda t: round(t[2] + np.random.laplace(0, 1.0/epsilon, 1)[0]), 
            axis=1)
        return result
        
