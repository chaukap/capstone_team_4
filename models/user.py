import pandas as pd

class user:
    def __init__(self, tuple):
        self.id = tuple[0]
        self.email = tuple[1]
        self.google_id = tuple[2]