import uuid
from datetime import datetime

class Transaction:
    def __init__(self, date: datetime = None, amount: float = 0.0, category: str = "", transaction_type: str = "", description: str = ""):
        self.__id = uuid.uuid4()  # Generates a random UUID
        self.date = date or datetime.now()  # Keep as datetime for calculations
        self.amount = amount
        self.category = category
        self.transaction_type = transaction_type
        self.description = description
    def to_tuple(self):
        return (
            str(self.__id),
            self.date,
            self.amount,
            self.category,
            self.transaction_type,
            self.description
        )
    def __repr__(self):
        return f"Amount: {self.amount}|Category: {self.category}|Description:{self.description}"
class Ledger:
    def __init__(self,db_connection):
        self.transaction = []
        self.db_connection = db_connection
    def add_transaction(self,transaction,db_connection):
        pass
