# Database — Online Banking System (SQLite)

## Tech Stack
- Python built-in sqlite3
- File: `data/banking.db` (auto-created)

---

## How to Create Tables
```bash
python database.py
```

---

## Tables — Exactly from Problem Statement

### 1. customers
```sql
-- Stores customer profile and login credentials
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,   -- UUID
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    phone       TEXT NOT NULL,
    address     TEXT NOT NULL,
    password_hash TEXT NOT NULL,    -- bcrypt hash — never plain text
    role        TEXT NOT NULL DEFAULT 'customer',
    created_at  TEXT NOT NULL
);
```

### 2. accounts
```sql
-- Stores bank accounts — each customer can have multiple
CREATE TABLE IF NOT EXISTS accounts (
    account_id   TEXT PRIMARY KEY,   -- UUID
    customer_id  TEXT NOT NULL REFERENCES customers(customer_id),
    account_type TEXT NOT NULL CHECK(account_type IN ('savings', 'current')),
    balance      REAL NOT NULL DEFAULT 0.0 CHECK(balance >= 0),
    status       TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
    created_at   TEXT NOT NULL
);
```

### 3. transactions
```sql
-- Records every fund transfer — both accounts updated in same transaction
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,  -- UUID
    from_account   TEXT NOT NULL REFERENCES accounts(account_id),
    to_account     TEXT NOT NULL REFERENCES accounts(account_id),
    amount         REAL NOT NULL CHECK(amount > 0),
    date           TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'completed'
                   CHECK(status IN ('completed', 'failed', 'pending'))
);
```

### 4. service_requests
```sql
-- Customer raises service requests — support staff resolves them
CREATE TABLE IF NOT EXISTS service_requests (
    request_id  TEXT PRIMARY KEY,  -- UUID
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    type        TEXT NOT NULL,
    description TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending', 'in-progress', 'resolved')),
    created_at  TEXT NOT NULL
);
```

### 5. bank_staff
```sql
-- Admin and support staff accounts
CREATE TABLE IF NOT EXISTS bank_staff (
    staff_id      TEXT PRIMARY KEY,  -- UUID
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,     -- bcrypt hash
    role          TEXT NOT NULL CHECK(role IN ('admin', 'support')),
    created_at    TEXT NOT NULL
);
```

---

## Relationships
```
customers
  └── accounts       (customer_id → customer_id)
  └── service_requests (customer_id → customer_id)

accounts
  └── transactions (from_account → account_id)
  └── transactions (to_account   → account_id)
```

---

## Critical: Fund Transfer Transaction

```sql
-- Both balance updates happen together or neither does
BEGIN;
  SELECT balance, status FROM accounts WHERE account_id = ?;
  -- if balance < amount → ROLLBACK
  UPDATE accounts SET balance = balance - amount WHERE account_id = from_account;
  UPDATE accounts SET balance = balance + amount WHERE account_id = to_account;
  INSERT INTO transactions (...) VALUES (...);
COMMIT;
```

---

## Key Queries

```sql
-- Customer: view own accounts
SELECT * FROM accounts WHERE customer_id = ?;

-- Customer: view own transactions
SELECT t.* FROM transactions t
JOIN accounts a ON t.from_account = a.account_id OR t.to_account = a.account_id
WHERE a.customer_id = ?;

-- Admin: all transactions
SELECT * FROM transactions ORDER BY date DESC;

-- Support: filter service requests by status
SELECT * FROM service_requests WHERE status = ?;
```

---

## Rules
- All IDs are UUIDs: `str(uuid.uuid4())`
- All timestamps: `datetime.now().isoformat()`
- `CREATE TABLE IF NOT EXISTS` — idempotent, safe to run multiple times
- Passwords stored as bcrypt hash — never plain text
- `balance` has `CHECK(balance >= 0)` — database-level protection
