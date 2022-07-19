from query_generator import query_generator
from mariadb_client import mariadb_client
import numpy as np
import pandas as pd
from typing import Callable, Any

class differential_privacy_engine:
    def __init__(self, username, password, host, database, port=3306):
        self.client = mariadb_client(
            username, password, host, database, port)
        return

    def __laplaceMechanismClamped(self, true_value, epsilon, u, l):
        range = abs(u - l)
        noise = np.random.laplace(0, range / epsilon, 1)[0]
        if noise >= u :
            noise = u
        else :
            if noise <= l:
                noise = l
        return true_value + noise

    def __noisy_average(self, noisy_sum, noisy_count, true_min, 
            true_max):
        if noisy_count <= 1:
            return (true_max - true_min)/2
        else:
            return noisy_sum / noisy_count

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
                lambda t: t[1] + np.random.laplace(0, 1.0/float(epsilon), 1)[0],
                axis=1)
        else:
            noisy_result.columns = [
                grouping_column, 
                count_column, 
                f"count_{count_column}"
            ]
            noisy_result[f"count_{count_column}"] = result.apply(
                lambda t: t[2] + np.random.laplace(0, 1.0/epsilon, 1)[0], 
                axis=1)

        result.columns = [grouping_column, count_column, "count"]
        noisy_result.columns = [grouping_column, count_column, "count"]
        return noisy_result, result

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

        noisy_result = result.copy(deep=True)

        noisy_result[f"sum_{sum_column}"] = noisy_result.apply(
            lambda t: int(self.__laplaceMechanismClamped(float(t[1]), epsilon, upper_bound, lower_bound)), 
            axis=1)
        return noisy_result, result
        
    def average(self, table, average_column, epsilon, lower_bound, upper_bound, grouping_column=None):
        sql_query = query_generator.generate_average_query(
            table, average_column, grouping_column)
        result = pd.DataFrame(
            self.client.execute_query(sql_query["query"])
        )

        if grouping_column == None:
            result.columns = [
                f"count_{average_column}",
                f"sum_{average_column}",
                f"min_{average_column}",
                f"max_{average_column}"]
        else:
            result.columns = [
                grouping_column, 
                f"count_{average_column}", 
                f"sum_{average_column}",
                f"min_{average_column}",
                f"max_{average_column}"]

        noisy_result = result.copy(deep=True)

        noisy_result[f"sum_{average_column}"] = noisy_result.apply(
            lambda t: int(self.__laplaceMechanismClamped(float(t[f"sum_{average_column}"]), epsilon, upper_bound, lower_bound)), 
            axis=1)
        noisy_result[f"count_{average_column}"] = noisy_result.apply(
            lambda t: t[f"count_{average_column}"] + np.random.laplace(0, 1.0/epsilon, 1)[0], 
            axis=1)
        noisy_result[f"average_{average_column}"] = noisy_result.apply(
            lambda t: self.__noisy_average(
                t[f"sum_{average_column}"],
                t[f"count_{average_column}"],
                t[f"min_{average_column}"],
                t[f"max_{average_column}"]), 
            axis=1)

        result[f"average_{average_column}"] = result.apply(
            lambda t: t[f"sum_{average_column}"] / t[f"count_{average_column}"], 
            axis=1)
        
        return noisy_result, result

    def exponential(self, table, column, scoring_function, epsilon, sensitivity: float=None):
        sql_query = query_generator.generate_generic_query(
            table, column)
        column = pd.Series(
            self.client.execute_query(sql_query["query"])
        )

        unique_values = column.unique()
        scores = [scoring_function(column, unique_value) for unique_value in unique_values]

        if sensitivity is None:
            sensitivity = max(scores) - min(scores)

        probabilities = [np.exp(epsilon * score / (2 * sensitivity)) for score in scores]
        probabilities = probabilities / np.linalg.norm(probabilities, ord=1)

        probability_distribution = pd.DataFrame({
            'values': unique_values, 
            'probabilities': probabilities
            })
        
        choice = np.random.choice(unique_values, 1, p=probabilities)[0]
        results = pd.DataFrame({
            'Answer': choice
        })

        return results, probability_distribution

    def exponential_options(self,
            table: str, column: str, scoring_function: Callable[[pd.Series, Any], float], 
            epsilons: list, sensitivity: float=None):

        sql_query = query_generator.generate_generic_query(
            table, column)
        column = pd.Series(
            self.client.execute_query(sql_query["query"])
        )

        unique_values = column.unique()
        scores = [scoring_function(column, unique_value) for unique_value in unique_values]

        if sensitivity is None:
            sensitivity = max(scores) - min(scores)

        probability_distribution = pd.DataFrame()
        for epsilon in epsilons:
            probabilities = [np.exp(epsilon * score / (2 * sensitivity)) for score in scores]
            probabilities = probabilities / np.linalg.norm(probabilities, ord=1)

            probability_distribution = probability_distribution.append(pd.DataFrame({
                'Value': unique_values, 
                'Probability': probabilities,
                'Epsilon': np.repeat(epsilon, len(unique_values))
                }))

        return probability_distribution