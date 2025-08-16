import uuid
from datetime import datetime
import random
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
# TRANSACTION CLASS
class Transaction:
    def __init__(self,userid,date: datetime = None, amount: float = 0.0, category: str = "", transaction_type: str = "", description: str = ""):
        self.userid = userid
        self.id = uuid.uuid4() # Generates a random UUID
        self.date = date or datetime.now()  # Keep as datetime for calculations
        self.amount = amount
        self.category = category
        self.transaction_type = transaction_type
        self.description = description
    def __repr__(self):
        return f"Amount: {self.amount}|Category: {self.category}|Description:{self.description}"
#USER CLASS
class User:
    def __init__(self, userid: int = None, first_name: str = '', last_name: str = ''):
        self.userid = userid if userid is not None else random.randint(1000, 9999)
        self.first_name = first_name.upper()
        self.last_name = last_name.upper()
        self.transactions = []
    def add_transaction(self, transaction):
        if not isinstance(transaction, Transaction):
            raise TypeError("Expected a Transaction object")
        self.transactions.append(transaction)
        return True
    def get_transaction(self):
        for transaction in self.transactions:
            return transaction
    def total_expenses(self, category):
        total = sum(t.amount for t in self.transactions
                    if isinstance(t, Transaction) and t.category == category)
        return f"{total} has been spent on {category}"
    def __repr__(self):
        return f'Id:{self.userid}|Customer: {self.first_name} {self.last_name}'
#DATABASE MANAGER CLASS
class DBMANAGER:
    def __init__(self):
        load_dotenv()
        #ESTABLISHING SQL CONNECTION
        # env keys: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT", 5432))
        )
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    def query(self, sql, params=None):
        self.cur.execute(sql, params or ())
        return self.cur.fetchall()
    #execute one query at a time
    def execute(self, sql, params=None, commit: bool = True):
        self.cur.execute(sql, params or ())
        if commit:
            self.conn.commit()
    #executing more than one query
    def executemany(self, sql, seq_of_params, commit: bool = True):
        self.cur.executemany(sql, seq_of_params)
        if commit:
            self.conn.commit()
    #closing connection
    def close(self):
        self.cur.close()
        self.conn.close()
    # creating tables for the Database
    def create_tables(self):
        self.execute(
        """CREATE TABLE IF NOT EXISTS USERS(
        user_id INTEGER PRIMARY KEY,
        f_name VARCHAR(100),
        l_name VARCHAR(100)
       );
       """) #tarnsaction table
        self.execute("""
            CREATE TABLE IF NOT EXISTS TRANSACTION(
            transaction_id UUID PRIMARY KEY,
            user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
            date TIMESTAMP NOT NULL,
            amount NUMERIC(10, 2) NOT NULL,
            category TEXT,
            transaction_type TEXT CHECK (transaction_type IN('income','expense','transfer')),
            description TEXT
            );
            """)
    #Function to insert user into the database
    def insert_user(self, user):
            if isinstance(user, User):
                self.cur.execute(
                    """
                    INSERT INTO USERS(user_id,f_name,l_name) 
                    VALUES (%s,%s,%s)""",
                    (user.userid, user.first_name, user.last_name)
                )
            self.conn.commit()  # Commit the transaction
    #function to insert transactions into the database
    def insert_transaction(self, transaction, user_id):
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction object")
        try:
            self.cur.execute(
                """
                INSERT INTO transaction (
                    transaction_id, user_id, date, amount, category, transaction_type, description
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(transaction.id), user_id, transaction.date, transaction.amount,
                transaction.category, transaction.transaction_type, transaction.description)
            )
            self.conn.commit()
        except Exception as e:
            print("Insert error:", e)
    #function to fetch users
    def fetch_user(self,user_id):
        self.cur.execute('SELECT * FROM users WHERE f_name = %s;', (user_id,))
        return self.cur.fetchall()
    def fetch_transactions_by_user(self, user_id):
        self.cur.execute("SELECT * FROM transaction WHERE user_id = %s;", (user_id,))
        return self.cur.fetchall()
    def delete_transactions(self,transaction_id):
        self.cur.execute("DELETE FROM TRANSACTION WHERE transaction_id = %s;",(transaction_id,))
        self.conn.commit()
        return f" Transaction {transaction_id} has been deleted"
#Ledger class handling main logic
class Ledger:
    def __init__(self, db_manager):
        self.users = []          # in-memory list of users
        self.db_manager = db_manager # handling database connectiion

    def add_user(self, user):
        self.users.append(user)

        self.db_manager.insert_user(user)

        return f"User {user.first_name} {user.last_name} added."
    def add_transaction(self, user_id, transaction):
        # Ensure transaction is valid
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction object")
        #Find the user in memory
        user = next((u for u in self.users if u.userid == user_id), None)
        if not user:
            raise ValueError(f"No user found with ID {user_id}")
        #Add to the user's transaction list
        user.transactions.append(transaction)

        self.db_manager.insert_transaction(transaction, user_id)

        return f"Transaction added for {user.first_name} {user.last_name}"
    def get_user(self,user_id): # Accessing users by their id
        user = [(u for u in self.users if u.userid == user_id)]
        if not user:
            raise ValueError('User does not exist')
        else:
            return self.db_manager.fetch_user(user_id)
    def get_user_transactions(self, user_id):
        # Ensure user_id exists in memory using list expression

        user = [(u for u in self.users if u.userid == user_id)]
        if not user:
            raise ValueError(f"No user found with ID {user_id}")
        return self.db_manager.fetch_transactions_by_user(user_id)