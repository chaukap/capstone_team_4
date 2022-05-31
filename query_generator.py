
class query_generator:
    def generate_count_query(self, table, identifier_column, grouping_column, count_column):
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