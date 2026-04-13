import sqlite3
import os

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/banking.db")
    
    # Create tables exactly as specified in the schema
    conn.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        email       TEXT UNIQUE NOT NULL,
        phone       TEXT NOT NULL,
        address     TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role        TEXT NOT NULL DEFAULT 'customer',
        created_at  TEXT NOT NULL
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id   TEXT PRIMARY KEY,
        customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
        account_type TEXT NOT NULL CHECK(account_type IN ('savings', 'current')),
        balance      REAL NOT NULL DEFAULT 0.0 CHECK(balance >= 0),
        status       TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
        created_at   TEXT NOT NULL
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        from_account   TEXT NOT NULL REFERENCES accounts(account_id),
        to_account     TEXT NOT NULL REFERENCES accounts(account_id),
        amount         REAL NOT NULL CHECK(amount > 0),
        date           TEXT NOT NULL,
        status         TEXT NOT NULL DEFAULT 'completed' CHECK(status IN ('completed', 'failed', 'pending'))
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS service_requests (
        request_id  TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL REFERENCES customers(customer_id),
        type        TEXT NOT NULL,
        description TEXT NOT NULL,
        status      TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'in-progress', 'resolved')),
        created_at  TEXT NOT NULL
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bank_staff (
        staff_id      TEXT PRIMARY KEY,
        email         TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role          TEXT NOT NULL CHECK(role IN ('admin', 'support')),
        created_at    TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect("data/banking.db")
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    init_db()
