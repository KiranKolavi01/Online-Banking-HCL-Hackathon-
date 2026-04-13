from fastapi import FastAPI, HTTPException
import uuid
from datetime import datetime
from database import get_db_connection
from models import (
    SignupRequest, SigninRequest, TransferRequest, 
    ServiceRequestInput, AdminCustomerRequest, 
    AdminAccountRequest, SupportUpdateRequest
)
from auth import hash_password, check_password

app = FastAPI()

def replace_none(data):
    if isinstance(data, dict):
        return {k: ("" if v is None else replace_none(v)) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_none(item) for item in data]
    return data

@app.post("/auth/signup")
def auth_signup(req: SignupRequest):
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    conn = get_db_connection()
    try:
        if req.role in ['admin', 'support']:
            row = conn.execute("SELECT email FROM bank_staff WHERE email=?", (req.email,)).fetchone()
            if row:
                raise HTTPException(status_code=400, detail="Email exists")
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO bank_staff (staff_id, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, req.email, hash_password(req.password), req.role, datetime.now().isoformat())
            )
            conn.commit()
            return replace_none({"user_id": user_id, "name": req.name, "role": req.role})
        else:
            row = conn.execute("SELECT email FROM customers WHERE email=?", (req.email,)).fetchone()
            if row:
                raise HTTPException(status_code=400, detail="Email exists")
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO customers (customer_id, name, email, phone, address, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, req.name, req.email, req.phone, req.address, hash_password(req.password), req.role, datetime.now().isoformat())
            )
            conn.commit()
            return replace_none({"user_id": user_id, "name": req.name, "role": req.role})
    finally:
        conn.close()

@app.post("/auth/signin")
def auth_signin(req: SigninRequest):
    conn = get_db_connection()
    try:
        # Check customers
        row = conn.execute("SELECT customer_id as user_id, name, role, password_hash FROM customers WHERE email=?", (req.email,)).fetchone()
        if not row:
            # Check bank_staff
            row = conn.execute("SELECT staff_id as user_id, role, password_hash FROM bank_staff WHERE email=?", (req.email,)).fetchone()
            
        if not row:
            raise HTTPException(status_code=401, detail="Wrong credentials")
            
        if not check_password(req.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Wrong credentials")
            
        name = row["name"] if "name" in row.keys() else ""
        return replace_none({"user_id": row["user_id"], "name": name, "role": row["role"]})
    finally:
        conn.close()

@app.get("/customer/{customer_id}/accounts")
def get_customer_accounts(customer_id: str):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT account_id, account_type, balance, status FROM accounts WHERE customer_id=?", (customer_id,)).fetchall()
        return replace_none([dict(r) for r in rows])
    finally:
        conn.close()

@app.get("/customer/{customer_id}/account/{account_id}")
def get_account_details(customer_id: str, account_id: str):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT account_id, customer_id, account_type, balance, status FROM accounts WHERE customer_id=? AND account_id=?", (customer_id, account_id)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        return replace_none(dict(row))
    finally:
        conn.close()

@app.post("/customer/transfer")
def customer_transfer(req: TransferRequest):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be > 0")
        
    conn = get_db_connection()
    try:
        conn.execute("BEGIN")
        row = conn.execute("SELECT balance, status FROM accounts WHERE account_id=?", (req.from_account,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        if row["status"] != "active":
            raise HTTPException(status_code=400, detail="Account inactive")
        if row["balance"] < req.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
            
        row_to = conn.execute("SELECT status FROM accounts WHERE account_id=?", (req.to_account,)).fetchone()
        if not row_to:
            raise HTTPException(status_code=404, detail="To account not found")
        if row_to["status"] != "active":
            raise HTTPException(status_code=400, detail="To account inactive")
            
        conn.execute("UPDATE accounts SET balance = balance - ? WHERE account_id=?", (req.amount, req.from_account))
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_id=?", (req.amount, req.to_account))
        
        tx_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO transactions (transaction_id, from_account, to_account, amount, date, status) VALUES (?, ?, ?, ?, ?, ?)",
            (tx_id, req.from_account, req.to_account, req.amount, datetime.now().isoformat(), "completed")
        )
        conn.commit()
        return replace_none({
            "transaction_id": tx_id, 
            "from_account": req.from_account, 
            "to_account": req.to_account, 
            "amount": req.amount, 
            "status": "completed"
        })
    except HTTPException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/customer/{customer_id}/transactions")
def get_customer_transactions(customer_id: str):
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT DISTINCT t.transaction_id, t.from_account, t.to_account, t.amount, t.date, t.status 
            FROM transactions t
            JOIN accounts a ON t.from_account = a.account_id OR t.to_account = a.account_id
            WHERE a.customer_id = ?
            ORDER BY t.date DESC
        """, (customer_id,)).fetchall()
        return replace_none([dict(r) for r in rows])
    finally:
        conn.close()


@app.post("/customer/service-request")
def create_service_request(req: ServiceRequestInput):
    conn = get_db_connection()
    try:
        req_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO service_requests (request_id, customer_id, type, description, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (req_id, req.customer_id, req.type, req.description, "pending", datetime.now().isoformat())
        )
        conn.commit()
        return replace_none({
            "request_id": req_id, 
            "customer_id": req.customer_id, 
            "type": req.type, 
            "description": req.description, 
            "status": "pending"
        })
    finally:
        conn.close()


@app.get("/customer/{customer_id}/service-requests")
def get_customer_service_requests(customer_id: str):
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT request_id, type, description, status FROM service_requests WHERE customer_id=?", (customer_id,)).fetchall()
        return replace_none([dict(r) for r in rows])
    finally:
        conn.close()


@app.post("/admin/customers")
def admin_create_customer(req: AdminCustomerRequest):
    conn = get_db_connection()
    try:
        user_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO customers (customer_id, name, email, phone, address, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, req.name, req.email, req.phone, req.address, hash_password(req.password), "customer", datetime.now().isoformat())
        )
        conn.commit()
        return replace_none({"customer_id": user_id, "name": req.name, "email": req.email})
    finally:
        conn.close()


@app.get("/admin/customers")
def admin_get_customers():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM customers").fetchall()
        return replace_none([dict(r) for r in rows])
    finally:
        conn.close()


@app.post("/admin/accounts")
def admin_create_account(req: AdminAccountRequest):
    conn = get_db_connection()
    try:
        acc_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO accounts (account_id, customer_id, account_type, balance, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (acc_id, req.customer_id, req.account_type, req.initial_balance, "active", datetime.now().isoformat())
        )
        conn.commit()
        return replace_none({
            "account_id": acc_id, 
            "customer_id": req.customer_id, 
            "account_type": req.account_type, 
            "balance": req.initial_balance, 
            "status": "active"
        })
    finally:
        conn.close()


@app.get("/admin/accounts")
def admin_get_accounts():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM accounts").fetchall()
        return replace_none([dict(r) for r in rows])
    finally:
        conn.close()


@app.get("/admin/transactions")
def admin_get_transactions():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM transactions").fetchall()
        return replace_none([dict(r) for r in rows])
    finally:
        conn.close()


@app.get("/support/service-requests")
def support_get_service_requests(status: str = ""):
    conn = get_db_connection()
    try:
        if status:
            rows = conn.execute("SELECT * FROM service_requests WHERE status=?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM service_requests").fetchall()
        return replace_none([dict(r) for r in rows])
    finally:
        conn.close()


@app.put("/support/service-requests/{request_id}")
def support_update_request(request_id: str, req: SupportUpdateRequest):
    if req.status not in ["pending", "in-progress", "resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = get_db_connection()
    try:
        conn.execute("UPDATE service_requests SET status=? WHERE request_id=?", (req.status, request_id))
        conn.commit()
        row = conn.execute("SELECT * FROM service_requests WHERE request_id=?", (request_id,)).fetchone()
        return replace_none(dict(row))
    finally:
        conn.close()
