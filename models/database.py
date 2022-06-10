class database:
    def __init__(self, tuple):
        self.id = tuple[0]
        self.database = tuple[1]
        self.host = tuple[2]
        self.username = tuple[3]
        self.password = tuple[4]
        self.user_id = tuple[5]
        self.table = tuple[6]
        self.name = tuple[7]
        self.description = tuple[8]
        self.port = tuple[9]