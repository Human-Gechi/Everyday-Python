# bank_app.py
from datetime import datetime, timedelta
import random
import uuid
import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
from getpass import getpass
import bcrypt
from typing import Optional

class Transaction:
    def __init__(self, transaction_type: str, amount: float, description: str = "", id: Optional[str] = None, date: Optional[datetime] = None):
        self.id = id or str(uuid.uuid4())
        self.transaction_type = transaction_type.lower()
        self.amount = float(amount)
        self.date = date or datetime.now()
        self.description = description

    def is_deposit(self):
        return self.transaction_type in ("deposit", "transfer_in", "interest")

    def is_withdrawal(self):
        return self.transaction_type in ("withdrawal", "transfer_out", "fee")

    def summary(self):
        return f"{self.date.isoformat()} | {self.transaction_type.upper():12} | {self.amount:10.2f} | {self.description}"

    def to_row(self, account_number: str, balance_after: float):
        return {
            "id": self.id,
            "account_number": account_number,
            "type": self.transaction_type,
            "amount": self.amount,
            "balance_after": balance_after,
            "timestamp": self.date,
            "description": self.description
        }

    @classmethod
    def from_row(cls, row):
        return cls(row["type"], row["amount"], row.get("description", ""), id=row["id"], date=row["timestamp"])


class Account:
    """Base account class. Handles deposit/withdraw and keeps transaction history.
       Now uses hashed PINs (bcrypt) """
    def __init__(self, holder_name: str, pin_hash: bytes, account_number: str, balance: float = 0.0, locked: bool = False):
        self.holder_name = holder_name
        self._pin_hash = pin_hash
        self.account_number = account_number
        self.balance = float(balance)
        self.locked = locked
        self.transactions: list[Transaction] = []

    def __str__(self):
        return f"{self.holder_name} | Acc#: {self.account_number} | Balance: {self.balance:.2f}"

    def display(self):
        return str(self)

    def authenticate(self, entered_pin: str) -> bool:
        """Verify plaintext entered_pin against stored bcrypt hash."""
        if not self._pin_hash:
            return False
        try:
            return bcrypt.checkpw(str(entered_pin).encode(), self._pin_hash)
        except Exception:
            return False

    def set_pin_hash(self, new_hash: bytes):
        self._pin_hash = new_hash

    def deposit(self, amount: float, description: str = "") -> Transaction | None:
        if amount <= 0:
            print("Invalid deposit amount.")
            return None
        self.balance += amount
        txn = Transaction("deposit", amount, description)
        self.transactions.append(txn)
        print(f"Deposited {amount:.2f} -> New balance: {self.balance:.2f}")
        return txn

    def withdraw(self, amount: float, entered_pin: str, description: str = "") -> Transaction | None:
        if self.locked:
            print("Account is locked. Withdrawal denied.")
            return None
        if not self.authenticate(entered_pin):
            print("Invalid PIN.")
            return None
        if amount <= 0 or amount > self.balance:
            print("Invalid withdrawal amount or insufficient funds.")
            return None
        self.balance -= amount
        txn = Transaction("withdrawal", amount, description)
        self.transactions.append(txn)
        print(f"Withdrew {amount:.2f} -> New balance: {self.balance:.2f}")
        return txn

    def add_transaction(self, transaction: Transaction):
        """Append an already-created transaction"""
        self.transactions.append(transaction)
        if transaction.is_deposit():
            self.balance += transaction.amount
        elif transaction.is_withdrawal():
            self.balance -= transaction.amount

    def show_transactions(self, limit: Optional[int] = None):
        items = self.transactions[-limit:] if limit is not None else self.transactions
        if not items:
            return "No transactions."
        return "\n".join(t.summary() for t in items)


class SavingsAccount(Account):
    def __init__(self, holder_name, pin_hash, account_number, balance=0.0, interest_rate=0.02):
        super().__init__(holder_name, pin_hash, account_number, balance)
        self.interest_rate = float(interest_rate)

    def add_interest(self):
        if self.balance <= 0:
            return 0.0
        interest = self.balance * self.interest_rate
        self.balance += interest
        txn = Transaction("interest", interest, "Interest credit")
        self.transactions.append(txn)
        print(f"Interest added: {interest:.2f} -> New balance: {self.balance:.2f}")
        return txn


class CurrentAccount(Account):
    def __init__(self, holder_name, pin_hash, account_number, balance=0.0, overdraft_limit=500.0):
        super().__init__(holder_name, pin_hash, account_number, balance)
        self.overdraft_limit = float(overdraft_limit)

    def withdraw(self, amount: float, entered_pin: str, description: str = "") -> Transaction | None:
        if self.locked:
            print("Account is locked. Withdrawal denied.")
            return None
        if not self.authenticate(entered_pin):
            print("Invalid PIN.")
            return None
        if amount <= 0:
            print("Invalid withdrawal amount.")
            return None
        if amount > (self.balance + self.overdraft_limit):
            print("Withdrawal exceeds overdraft limit.")
            return None
        # allow overdraft
        self.balance -= amount
        txn = Transaction("withdrawal", amount, description)
        self.transactions.append(txn)
        print(f"Withdrew {amount:.2f} (with overdraft) -> New balance: {self.balance:.2f}")
        return txn


class FixedDepositAccount(Account):
    def __init__(self, holder_name, pin_hash, account_number, balance=0.0, lock_period_days=30):
        super().__init__(holder_name, pin_hash, account_number, balance)
        self.start_date = datetime.now()
        self.lock_date = self.start_date + timedelta(days=int(lock_period_days))

    def withdraw(self, amount: float, entered_pin: str, description: str = "") -> Transaction | None:
        if datetime.now() < self.lock_date:
            print(f"Account locked till {self.lock_date.date()}. Withdrawal denied.")
            return None
        return super().withdraw(amount, entered_pin, description)

    def get_start_date(self):
        return self.start_date

    def get_lock_date(self):
        return self.lock_date

class AuthSystem:
    MAX_FAILED_ATTEMPTS = 3

    def __init__(self):
        self.failed_attempts: dict[str, int] = {}  # account_number -> count

    def verify_pin(self, account: Account, input_pin: str) -> bool:
        if account.locked:
            print("Account is locked. Please contact the bank.")
            return False
        if account.authenticate(input_pin):
            # reset counter
            self.failed_attempts[account.account_number] = 0
            return True
        # failed
        count = self.failed_attempts.get(account.account_number, 0) + 1
        self.failed_attempts[account.account_number] = count
        print(f"Invalid PIN. Failed attempts: {count}/{self.MAX_FAILED_ATTEMPTS}")
        if count >= self.MAX_FAILED_ATTEMPTS:
            account.locked = True
            print("Account locked due to too many failed attempts.")
        return False

    def change_pin(self, account: Account, old_pin: str, new_pin: str) -> bool:
        if self.verify_pin(account, old_pin):
            new_hash = bcrypt.hashpw(str(new_pin).encode(), bcrypt.gensalt())
            account.set_pin_hash(new_hash)
            print("PIN changed successfully.")
            return True
        print("PIN change failed.")
        return False

    def is_account_locked(self, account: Account) -> bool:
        return account.locked

    def reset_failed_attempts(self, account: Account):
        self.failed_attempts[account.account_number] = 0

class Database:
    def __init__(self):
        load_dotenv()
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

    def execute(self, sql, params=None, commit: bool = True):
        self.cur.execute(sql, params or ())
        if commit:
            self.conn.commit()

    def executemany(self, sql, seq_of_params, commit: bool = True):
        self.cur.executemany(sql, seq_of_params)
        if commit:
            self.conn.commit()

    def close(self):
        self.cur.close()
        self.conn.close()

    def create_tables(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_number TEXT PRIMARY KEY,
            holder_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            pin_hash BYTEA NOT NULL,
            balance REAL DEFAULT 0,
            locked BOOLEAN DEFAULT FALSE,
            extra JSONB DEFAULT '{}'::jsonb, -- for storing overdraft_limit, interest_rate, lock_period etc.
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id UUID PRIMARY KEY,
            account_number TEXT REFERENCES accounts(account_number) ON DELETE CASCADE,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
        """)
class Bank:
    def __init__(self, name: str, db: Database):
        self.name = name
        self.db = db
        self.accounts: dict[str, Account] = {}
        self.db.create_tables()
        self.load_accounts_from_db()

    def _generate_account_number(self) -> str:
        while True:
            acc_num = str(random.randint(10**9, 10**10 - 1))
            if acc_num not in self.accounts and not self._account_exists_in_db(acc_num):
                return acc_num

    def _account_exists_in_db(self, acc_num: str) -> bool:
        rows = self.db.query("SELECT 1 FROM accounts WHERE account_number=%s LIMIT 1", (acc_num,))
        return bool(rows)

    def load_accounts_from_db(self):
        """Load accounts and recent transactions from DB into memory."""
        rows = self.db.query("SELECT * FROM accounts")
        for r in rows:
            acct_type = r["account_type"]
            pin_hash = bytes(r["pin_hash"]) if r["pin_hash"] is not None else b""
            acc_num = r["account_number"]
            extra = r.get("extra") or {}
            balance = r["balance"] or 0.0
            locked = bool(r.get("locked", False))

            if acct_type == "savings":
                acct = SavingsAccount(r["holder_name"], pin_hash, acc_num, balance, interest_rate=extra.get("interest_rate", 0.02))
            elif acct_type == "current":
                acct = CurrentAccount(r["holder_name"], pin_hash, acc_num, balance, overdraft_limit=extra.get("overdraft_limit", 500.0))
            elif acct_type == "fixed":
                acct = FixedDepositAccount(r["holder_name"], pin_hash, acc_num, balance, lock_period_days=extra.get("lock_period_days", 30))
            else:
                acct = Account(r["holder_name"], pin_hash, acc_num, balance)
            acct.locked = locked
            # load transactions for this account
            tx_rows = self.db.query("SELECT id, type, amount, balance_after, timestamp, description FROM transactions WHERE account_number=%s ORDER BY timestamp ASC", (acc_num,))
            for txr in tx_rows:
                txn = Transaction.from_row(txr)
                acct.transactions.append(txn)
            self.accounts[acc_num] = acct

    def create_account(self, account_type: str, holder_name: str, initial_deposit: float = 0.0, **kwargs) -> Optional[Account]:
        acc_num = self._generate_account_number()
        account_type = account_type.strip().lower()
        raw_pin = getpass("Set a 4+ digit PIN (hidden): ").strip()
        if len(raw_pin) < 4:
            print("PIN too short. Must be at least 4 characters.")
            return None
        pin_hash = bcrypt.hashpw(raw_pin.encode(), bcrypt.gensalt())

        if account_type == "savings":
            acct = SavingsAccount(holder_name, pin_hash, acc_num, initial_deposit, interest_rate=kwargs.get("interest_rate", 0.02))
        elif account_type == "current":
            acct = CurrentAccount(holder_name, pin_hash, acc_num, initial_deposit, overdraft_limit=kwargs.get("overdraft_limit", 500.0))
        elif account_type in ("fixed", "fixeddeposit", "fixed_deposit"):
            acct = FixedDepositAccount(holder_name, pin_hash, acc_num, initial_deposit, lock_period_days=kwargs.get("lock_period_days", 30))
        else:
            print("Invalid account type")
            return None

        self.accounts[acc_num] = acct
        extra = {}
        if isinstance(acct, SavingsAccount):
            extra["interest_rate"] = acct.interest_rate
        if isinstance(acct, CurrentAccount):
            extra["overdraft_limit"] = acct.overdraft_limit
        if isinstance(acct, FixedDepositAccount):
            extra["lock_period_days"] = (acct.lock_date - acct.start_date).days

        self.db.execute(
            "INSERT INTO accounts (account_number, holder_name, account_type, pin_hash, balance, locked, extra) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (acc_num, holder_name, account_type, psycopg2.Binary(pin_hash), acct.balance, acct.locked, psycopg2.extras.Json(extra))
        )

        # log the initial deposit as a transaction if > 0
        if initial_deposit > 0:
            txn = Transaction("deposit", initial_deposit, "Initial deposit")
            self.db.execute(
                "INSERT INTO transactions (id, account_number, type, amount, balance_after, timestamp, description) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (txn.id, acc_num, txn.transaction_type, txn.amount, acct.balance, txn.date, txn.description)
            )
            acct.transactions.append(txn)

        print(f"{account_type.title()} account created for {holder_name}. Account number: {acc_num}")
        return acct

    def find_account(self, account_number: str) -> Optional[Account]:
        return self.accounts.get(account_number)

    def _persist_account_balance_and_lock(self, acct: Account):
        self.db.execute(
            "UPDATE accounts SET balance=%s, locked=%s WHERE account_number=%s",
            (acct.balance, acct.locked, acct.account_number)
        )

    def _log_transaction(self, acct: Account, txn: Transaction):
        self.db.execute(
            "INSERT INTO transactions (id, account_number, type, amount, balance_after, timestamp, description) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (txn.id, acct.account_number, txn.transaction_type, txn.amount, acct.balance, txn.date, txn.description)
        )

    def deposit(self, account_number: str, amount: float, description: str = ""):
        acct = self.find_account(account_number)
        if not acct:
            print("Account not found.")
            return
        txn = acct.deposit(amount, description)
        if txn:
            self._persist_account_balance_and_lock(acct)
            self._log_transaction(acct, txn)

    def withdraw(self, account_number: str, amount: float, auth_system: AuthSystem, description: str = ""):
        acct = self.find_account(account_number)
        if not acct:
            print("Account not found.")
            return
        pin = getpass("Enter your PIN (hidden): ").strip()
        if not auth_system.verify_pin(acct, pin):
            return
        txn = acct.withdraw(amount, pin, description)
        if txn:
            self._persist_account_balance_and_lock(acct)
            self._log_transaction(acct, txn)

    def transfer(self, from_acc_num: str, to_acc_num: str, amount: float, auth_system: AuthSystem, description: str = ""):
        from_acc = self.find_account(from_acc_num)
        to_acc = self.find_account(to_acc_num)
        if not from_acc or not to_acc:
            print("One or both accounts not found.")
            return
        pin = getpass("Enter your PIN (hidden): ").strip()
        if not auth_system.verify_pin(from_acc, pin):
            print("Transfer failed due to PIN verification.")
            return
        # attempt withdrawal
        withdraw_txn = from_acc.withdraw(amount, pin, f"Transfer to {to_acc_num}. {description}")
        if not withdraw_txn:
            print("Transfer failed during withdrawal.")
            return
        # deposit to destination
        deposit_txn = to_acc.deposit(amount, f"Transfer from {from_acc_num}. {description}")

        # append explicit transfer_in/out transaction records
        transfer_out = Transaction("transfer_out", amount, f"To {to_acc_num}. {description}")
        transfer_in = Transaction("transfer_in", amount, f"From {from_acc_num}. {description}")

        from_acc.transactions.append(transfer_out)
        to_acc.transactions.append(transfer_in)

        # persist balances and log all transactions
        self._persist_account_balance_and_lock(from_acc)
        self._persist_account_balance_and_lock(to_acc)

        # log: withdrawal, deposit, transfer_out, transfer_in (we can log the final ones)
        self._log_transaction(from_acc, transfer_out)
        self._log_transaction(to_acc, transfer_in)

        print("Transfer completed successfully.")

    def change_pin(self, account_number: str, auth_system: AuthSystem):
        acct = self.find_account(account_number)
        if not acct:
            print("Account not found.")
            return
        old_pin = getpass("Enter current PIN (hidden): ").strip()
        if not auth_system.verify_pin(acct, old_pin):
            return
        new_pin = getpass("Enter new PIN (hidden): ").strip()
        if len(new_pin) < 4:
            print("New PIN too short.")
            return
        new_hash = bcrypt.hashpw(new_pin.encode(), bcrypt.gensalt())
        acct.set_pin_hash(new_hash)
        # persist to DB
        self.db.execute("UPDATE accounts SET pin_hash=%s WHERE account_number=%s", (psycopg2.Binary(new_hash), acct.account_number))
        print("PIN changed and persisted to DB.")

    def transaction_history(self, account_number: str, limit: Optional[int] = 50):
        acct = self.find_account(account_number)
        if not acct:
            print("Account not found.")
            return
        rows = self.db.query("SELECT id, type, amount, balance_after, timestamp, description FROM transactions WHERE account_number=%s ORDER BY timestamp DESC LIMIT %s", (account_number, limit))
        if not rows:
            print("No transactions found.")
            return
        for r in rows:
            ts = r["timestamp"].isoformat() if r["timestamp"] else "?"
            print(f"{ts} | {r['type'].upper():12} | {r['amount']:10.2f} | bal_after: {r['balance_after']:10.2f} | {r.get('description') or ''}")

def main():
    load_dotenv()
    db = Database()
    bank = Bank("MyBank", db)
    auth = AuthSystem()

    # demo menu
    while True:
        print("\n=== MyBank CLI ===")
        print("1) Create account")
        print("2) Deposit")
        print("3) Withdraw")
        print("4) Transfer")
        print("5) Show account")
        print("6) Transaction history")
        print("7) Change PIN")
        print("8) Exit")
        choice = input("Choice: ").strip()

        if choice == "1":
            acct_type = input("Type (savings/current/fixed): ").strip()
            holder = input("Account holder name: ").strip()
            init_dep = float(input("Initial deposit (0 if none): ").strip() or 0.0)
            acct = bank.create_account(acct_type, holder, initial_deposit=init_dep)
            if acct:
                print("Created:", acct.display())

        elif choice == "2":
            acc = input("Account number: ").strip()
            amt = float(input("Amount: ").strip())
            desc = input("Description (optional): ").strip()
            bank.deposit(acc, amt, desc)

        elif choice == "3":
            acc = input("Account number: ").strip()
            amt = float(input("Amount: ").strip())
            desc = input("Description (optional): ").strip()
            bank.withdraw(acc, amt, auth, desc)

        elif choice == "4":
            src = input("From account: ").strip()
            dst = input("To account: ").strip()
            amt = float(input("Amount: ").strip())
            desc = input("Description (optional): ").strip()
            bank.transfer(src, dst, amt, auth, desc)

        elif choice == "5":
            acc = input("Account number: ").strip()
            a = bank.find_account(acc)
            if a:
                print(a.display())
            else:
                print("Not found.")

        elif choice == "6":
            acc = input("Account number: ").strip()
            limit = input("Limit(enter for 50): ").strip()
            limit = int(limit) if limit else 50
            bank.transaction_history(acc, limit)

        elif choice == "7":
            acc = input("Account number: ").strip()
            bank.change_pin(acc, auth)

        elif choice == "8":
            print("Bye.")
            db.close()
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
