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
        noisy_result = result.copy(deep=True)
        if grouping_column == None:
            noisy_result.columns = [f"count_{count_column}"]
            noisy_result[f"count_{count_column}"] = result.apply(
                lambda t: t[1] + np.random.laplace(0, 2.0/float(epsilon), 1)[0],
                axis=1)
        else:
            noisy_result.columns = [
                grouping_column, 
                count_column, 
                f"count_{count_column}"
            ]
            noisy_result[f"count_{count_column}"] = result.apply(
                lambda t: t[2] + np.random.laplace(0, 2.0/epsilon, 1)[0], 
                axis=1)

        result.columns = [grouping_column, count_column, "count"]
        noisy_result.columns = [grouping_column, count_column, "count"]
        return noisy_result, result

    def sum(self, table, sum_column, epsilon, lower_bound, upper_bound, grouping_column = None):
        sql_query = query_generator.generate_sum_query(
            table, sum_column, grouping_column)
        noisy_result = pd.DataFrame(
            self.client.execute_query(sql_query["query"])
        )
        if grouping_column == None:
            noisy_result.columns = [f"sum_{sum_column}"]
        else:
            noisy_result.columns = [grouping_column, f"sum_{sum_column}"]

        noisy_result[f"sum_{sum_column}"] = noisy_result.apply(
            lambda t: int(self.__laplaceMechanismClamped(float(t[1]), epsilon, upper_bound, lower_bound)), 
            axis=1)
        return noisy_result, 0
        
