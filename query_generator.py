
class query_generator:
    def generate_count_query(table, identifier_column, grouping_column, count_column):
        """Generate an SQL query that returns the count of one column grouped by another.

           Parameters
           ----------
           table : str,
           identifier_column : str,
           grouping_column : str,
           count_column : str,
           
           Returns
           ----------
           A dict with two entries:
           query: A string containing the SQL query that will satisfy the requirements.
           multiple_contributors: A string containing an SQL query that will identify
               users that contributed more than once to the results. """
        return {
            "query": f"""
                SELECT {grouping_column}, {count_column}, COUNT({grouping_column})
                FROM {table}
                GROUP BY {grouping_column}, {count_column}""",

            "multiple_contributors": f"""
                SELECT {identifier_column}, {grouping_column}, {count_column}, Count({count_column}) 
                FROM {table}
                WHERE {identifier_column} in (
                    SELECT {identifier_column} FROM Arrests
                    GROUP BY {identifier_column}
                    HAVING Count({identifier_column}) > 1
                )
                GROUP BY Id, {grouping_column}, {count_column}"""
        }