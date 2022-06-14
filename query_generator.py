
from ast import AsyncFunctionDef


class query_generator:
    def generate_count_query(table, count_column, grouping_column = None):
        """Generate an SQL query that returns the count of one column grouped by another.

           Parameters
           ----------
           table : str,
           identifier_column : str,
           grouping_column : str,
           count_column : str,
           
           Returns
           ----------
           A dict:
           query: A string containing the SQL query that will satisfy the requirements."""
        if grouping_column == None:
            return {
                "query": f"""
                    SELECT COUNT({count_column}) FROM {table}
                """
            }
        return {
            "query": f"""
                SELECT {grouping_column}, {count_column}, COUNT({grouping_column})
                FROM {table}
                GROUP BY {grouping_column}, {count_column}"""
        }
    
    def generate_sum_query(table, sum_column, grouping_column = None):
        query = ""
        if grouping_column == None:
            query = {
                "query": f"""
                    SELECT SUM({sum_column}) FROM {table}
                """
            }
        else:
            query =  {
                "query": f"""
                    SELECT {grouping_column}, SUM({sum_column}) FROM {table}
                    GROUP BY {grouping_column}
                """
            }

        return query


    def generate_average_query(table, average_column, grouping_column = None):
        if grouping_column == None:
            query = {
                "query": f"""
                    SELECT COUNT({average_column}), 
                        SUM({average_column}) ,
                        MIN({average_column}),
                        MAX({average_column})
                    FROM {table} 
                """
            }
        else:
            query = {
                "query": f"""
                    SELECT {grouping_column}, 
                        COUNT({average_column}), 
                        SUM({average_column}),
                        MIN({average_column}),
                        MAX({average_column})
                    FROM {table} 
                    GROUP BY {grouping_column}
                """
            }
        return query
