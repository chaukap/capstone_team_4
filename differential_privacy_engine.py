from query_generator import query_generator
from mariadb_client import mariadb_client
import numpy as np
import pandas as pd

class differential_privacy_engine:
    def __init__(self, username, password, host, database, port=3306):
        self.client = mariadb_client(
            username, password, host, database, port)
        return

    def __laplaceMechanismClamped(self, true_value, epsilon, u, l):
        range = abs(u - l)
        noise = np.random.laplace(0, 2 * range / epsilon, 1)[0]
        if noise >= u :
            noise = u
        else :
            if noise <= l:
                noise = l
        return true_value + noise


    def count(self, table, count_column, epsilon, grouping_column = None):
        sql_query = query_generator.generate_count_query(
            table, count_column, grouping_column)
        result = pd.DataFrame(
            self.client.execute_query(sql_query["query"])
        )
        if grouping_column == None:
            result.columns = [f"count_{count_column}"]
        else:
            result.columns = [grouping_column, count_column, f"count_{count_column}"]
        result[f"count_{count_column}"] = result.apply(
            lambda t: round(t[2] + np.random.laplace(0, 1.0/epsilon, 1)[0]), 
            axis=1)
        return result

    def sum(self, table, sum_column, epsilon, lower_bound, upper_bound, grouping_column = None):
        sql_query = query_generator.generate_sum_query(
            table, sum_column, grouping_column)
        result = pd.DataFrame(
            self.client.execute_query(sql_query["query"])
        )
        if grouping_column == None:
            result.columns = [f"sum_{sum_column}"]
        else:
            result.columns = [grouping_column, f"sum_{sum_column}"]
        result[f"sum_{sum_column}"] = result.apply(
            lambda t: int(self.__laplaceMechanismClamped(float(t[1]), epsilon, upper_bound, lower_bound)), 
            axis=1)
        return result
        
