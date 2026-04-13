import sqlite3
import uuid
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path="data/banking.db"):
        self.db_path = db_path
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        """Initializes the database tables based on requirements."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                phone       TEXT NOT NULL,
                address     TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role        TEXT NOT NULL DEFAULT 'customer',
                created_at  TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id   TEXT PRIMARY KEY,
                customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
                account_type TEXT NOT NULL CHECK(account_type IN ('savings', 'current')),
                balance      REAL NOT NULL DEFAULT 0.0 CHECK(balance >= 0),
                status       TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
                created_at   TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                from_account   TEXT NOT NULL REFERENCES accounts(account_id),
                to_account     TEXT NOT NULL REFERENCES accounts(account_id),
                amount         REAL NOT NULL CHECK(amount > 0),
                date           TEXT NOT NULL,
                status         TEXT NOT NULL DEFAULT 'completed'
                               CHECK(status IN ('completed', 'failed', 'pending'))
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS service_requests (
                request_id  TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL REFERENCES customers(customer_id),
                type        TEXT NOT NULL,
                description TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending', 'in-progress', 'resolved')),
                created_at  TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS bank_staff (
                staff_id      TEXT PRIMARY KEY,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL CHECK(role IN ('admin', 'support')),
                created_at    TEXT NOT NULL
            );
            """
        ]
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)
            conn.commit()
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
        finally:
            conn.close()

    # --- Customer Methods ---
    def create_customer(self, name, email, phone, address, password_hash, role='customer'):
        customer_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (customer_id, name, email, phone, address, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (customer_id, name, email, phone, address, password_hash, role, created_at))
            conn.commit()
            return customer_id
        except sqlite3.IntegrityError as e:
            print(f"Error: Email {email} already exists.")
            return None
        finally:
            conn.close()

    def get_customer_by_email(self, email):
        conn = self.get_connection()
        customer = conn.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
        conn.close()
        return dict(customer) if customer else None

    # --- Account Methods ---
    def create_account(self, customer_id, account_type, initial_balance=0.0):
        account_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO accounts (account_id, customer_id, account_type, balance, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (account_id, customer_id, account_type, initial_balance, created_at))
            conn.commit()
            return account_id
        except sqlite3.Error as e:
            print(f"Error creating account: {e}")
            return None
        finally:
            conn.close()

    def get_customer_accounts(self, customer_id):
        conn = self.get_connection()
        accounts = conn.execute("SELECT * FROM accounts WHERE customer_id = ?", (customer_id,)).fetchall()
        conn.close()
        return [dict(a) for a in accounts]

    # --- Transaction Methods ---
    def transfer_funds(self, from_account_id, to_account_id, amount):
        """Executes a fund transfer atomically."""
        transaction_id = str(uuid.uuid4())
        date = datetime.now().isoformat()
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Check sender balance and status
            from_account = cursor.execute("SELECT balance, status FROM accounts WHERE account_id = ?", (from_account_id,)).fetchone()
            if not from_account:
                raise ValueError("Sender account not found.")
            if from_account['status'] != 'active':
                raise ValueError("Sender account is not active.")
            if from_account['balance'] < amount:
                raise ValueError("Insufficient balance.")

            # 2. Check receiver account
            to_account = cursor.execute("SELECT status FROM accounts WHERE account_id = ?", (to_account_id,)).fetchone()
            if not to_account:
                raise ValueError("Receiver account not found.")
            if to_account['status'] != 'active':
                raise ValueError("Receiver account is not active.")

            # 3. Deduct from sender
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, from_account_id))
            
            # 4. Add to receiver
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, to_account_id))
            
            # 5. Record transaction
            cursor.execute("""
                INSERT INTO transactions (transaction_id, from_account, to_account, amount, date, status)
                VALUES (?, ?, ?, ?, ?, 'completed')
            """, (transaction_id, from_account_id, to_account_id, amount, date))
            
            conn.commit()
            print(f"Transfer of {amount} from {from_account_id} to {to_account_id} successful.")
            return transaction_id
        except Exception as e:
            conn.rollback()
            print(f"Transaction failed: {e}")
            return None
        finally:
            conn.close()

    def get_transaction_history(self, customer_id):
        conn = self.get_connection()
        query = """
            SELECT t.* FROM transactions t
            JOIN accounts a ON t.from_account = a.account_id OR t.to_account = a.account_id
            WHERE a.customer_id = ?
            ORDER BY t.date DESC
        """
        transactions = conn.execute(query, (customer_id,)).fetchall()
        conn.close()
        return [dict(t) for t in transactions]

    # --- Admin/Staff Methods ---
    def create_staff(self, email, password_hash, role):
        staff_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bank_staff (staff_id, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (staff_id, email, password_hash, role, created_at))
            conn.commit()
            return staff_id
        except sqlite3.Error as e:
            print(f"Error creating staff: {e}")
            return None
        finally:
            conn.close()

    def get_all_transactions(self):
        conn = self.get_connection()
        transactions = conn.execute("SELECT * FROM transactions ORDER BY date DESC").fetchall()
        conn.close()
        return [dict(t) for t in transactions]

    # --- Service Request Methods ---
    def create_service_request(self, customer_id, req_type, description):
        request_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO service_requests (request_id, customer_id, type, description, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (request_id, customer_id, req_type, description, created_at))
            conn.commit()
            return request_id
        except sqlite3.Error as e:
            print(f"Error creating service request: {e}")
            return None
        finally:
            conn.close()

    def get_service_requests_by_status(self, status):
        conn = self.get_connection()
        requests = conn.execute("SELECT * FROM service_requests WHERE status = ?", (status,)).fetchall()
        conn.close()
        return [dict(r) for r in requests]

# If run directly, initialize the database
if __name__ == "__main__":
    db = DatabaseManager()
