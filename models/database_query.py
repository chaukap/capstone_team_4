class database_query:
    def __init__(self, tuple):
        self.id = tuple[0]
        self.database_id = tuple[1]
        self.statistic = tuple[2]
        self.query_type = tuple[3]
        self.grouping_column = tuple[4]
        self.epsilon = tuple[5]
        self.upper_bound = tuple[6]
        self.lower_bound = tuple[7]