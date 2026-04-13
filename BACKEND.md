# Backend — Online Banking: Customer Account & Transaction Management System

## Tech Stack
- Python 3.10+
- FastAPI
- SQLite (built-in sqlite3)
- bcrypt
- uvicorn

---

## How to Run
```bash
python database.py   # creates all tables
uvicorn main:app --reload
# http://127.0.0.1:8000
# Swagger docs: http://127.0.0.1:8000/docs
```

---

## Folder Structure
```
banking/
├── main.py          # FastAPI app — all routes
├── database.py      # SQLite connection + table creation
├── models.py        # Pydantic input validation models
├── auth.py          # signup, signin, bcrypt hashing
├── requirements.txt
└── data/
    └── banking.db   # SQLite file (auto-created)
```

---

## Data Flow
```
Request → Role Check → Input Validation → Business Logic → SQLite → JSON Response
```

---

## Three Roles
- **Customer** — view account, transfer funds, raise service requests
- **Admin** — manage customers, accounts, view all transactions
- **Support** — view and update service requests

---

## Auth

### POST /auth/signup
```
# Creates new user — hashes password with bcrypt before storing
Body: { name, email, phone, address, password, role }
role: customer / admin / support
Validates: email unique, password min 8 chars
Returns: { user_id, name, role }
HTTP 400 if email exists
```

### POST /auth/signin
```
# Verifies credentials — returns role for session
Body: { email, password }
Validates: email exists, bcrypt.checkpw() matches
Returns: { user_id, name, role }
HTTP 401 if wrong credentials
```

---

## Customer Endpoints

### GET /customer/{customer_id}/accounts
```
# Returns all accounts belonging to this customer
Returns: [ { account_id, account_type, balance, status } ]
```

### GET /customer/{customer_id}/account/{account_id}
```
# Returns account details and current balance
Returns: { account_id, customer_id, account_type, balance, status }
HTTP 404 if account not found
```

### POST /customer/transfer
```
# Transfers funds from one account to another — updates both balances atomically
Body: { from_account, to_account, amount }
Validates:
  - amount must be > 0
  - from_account must have sufficient balance
  - from_account status must be active
  - to_account must exist and be active
Uses SQLite transaction:
  BEGIN
    check from_account balance >= amount
    UPDATE from_account balance = balance - amount
    UPDATE to_account balance = balance + amount
    INSERT transaction record (status=completed)
  COMMIT
Returns: { transaction_id, from_account, to_account, amount, status: completed }
HTTP 400 if insufficient balance
HTTP 400 if account inactive
```

### GET /customer/{customer_id}/transactions
```
# Returns all transactions for all accounts of this customer
Returns: [ { transaction_id, from_account, to_account, amount, date, status } ]
```

### POST /customer/service-request
```
# Customer raises a service request
Body: { customer_id, type, description }
Sets status = pending
Returns: { request_id, customer_id, type, description, status }
```

### GET /customer/{customer_id}/service-requests
```
# Returns all service requests raised by this customer
Returns: [ { request_id, type, description, status } ]
```

---

## Admin Endpoints

### POST /admin/customers
```
# Admin creates a new customer account
Body: { name, email, phone, address, password }
Hashes password with bcrypt
Returns: { customer_id, name, email }
```

### GET /admin/customers
```
# Returns all customers
Returns: list of all customer records
```

### POST /admin/accounts
```
# Admin creates a bank account for a customer
Body: { customer_id, account_type, initial_balance }
account_type: savings / current
Sets status = active
Returns: { account_id, customer_id, account_type, balance, status }
```

### GET /admin/accounts
```
# Returns all accounts across all customers
Returns: list of all account records
```

### GET /admin/transactions
```
# Returns all transactions in the system
Returns: list of all transaction records
```

---

## Support Endpoints

### GET /support/service-requests
```
# Returns all service requests across all customers
Query params: status (optional) — pending / in-progress / resolved
Returns: list of service request records
```

### PUT /support/service-requests/{request_id}
```
# Support staff updates the status of a service request
Body: { status }
status must be: pending / in-progress / resolved
Returns: updated service request record
HTTP 400 if invalid status
```

---

## Fund Transfer — Transaction Safety

```python
# Most important data engineering part — atomic balance update
# Both accounts update together or neither does

def transfer_funds(from_account, to_account, amount):
    conn = sqlite3.connect("data/banking.db")
    try:
        conn.execute("BEGIN")

        # Check balance inside transaction
        row = conn.execute(
            "SELECT balance, status FROM accounts WHERE account_id=?",
            (from_account,)
        ).fetchone()

        if row["status"] != "active":
            raise ValueError("Account is not active")
        if row["balance"] < amount:
            raise ValueError("Insufficient balance")

        # Deduct from sender
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE account_id=?",
            (amount, from_account)
        )
        # Add to receiver
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE account_id=?",
            (amount, to_account)
        )
        # Record the transaction
        conn.execute(
            "INSERT INTO transactions (transaction_id,from_account,to_account,amount,date,status) VALUES (?,?,?,?,?,?)",
            (str(uuid4()), from_account, to_account, amount, datetime.now().isoformat(), "completed")
        )
        conn.commit()
    except Exception as e:
        conn.rollback()  # undo everything if anything failed
        raise e
    finally:
        conn.close()
```

---

## Error Handling
```python
# Every endpoint wrapped in try/except
# Pydantic handles invalid input — HTTP 422 automatically
# Business rule violations — HTTP 400 with message
# Not found — HTTP 404
# Wrong role — HTTP 403
# All JSON responses replace None with empty string before returning
```

---

## Requirements.txt
```
fastapi
uvicorn[standard]
bcrypt
pydantic
python-multipart
```
