from fastapi import FastAPI, HTTPException
import uuid
from datetime import datetime
from database import db
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
    
    try:
        if req.role in ['admin', 'support']:
            user_id = db.create_staff(req.email, hash_password(req.password), req.role)
        else:
            user_id = db.create_customer(req.name, req.email, req.phone, req.address, hash_password(req.password), req.role)
        
        return replace_none({"user_id": user_id, "name": req.name, "role": req.role})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/signin")
def auth_signin(req: SigninRequest):
    row = db.get_customer_by_email(req.email)
    
    if row:
        user_id = row["customer_id"]
        role = row["role"]
        pwd_hash = row["password_hash"]
        name = row["name"]
    else:
        row = db.get_staff_by_email(req.email)
        if row:
            user_id = row["staff_id"]
            role = row["role"]
            pwd_hash = row["password_hash"]
            name = ""
        else:
            raise HTTPException(status_code=401, detail="Wrong credentials")
            
    if not check_password(req.password, pwd_hash):
        raise HTTPException(status_code=401, detail="Wrong credentials")
        
    return replace_none({"user_id": user_id, "name": name, "role": role})

@app.get("/customer/{customer_id}/accounts")
def get_customer_accounts(customer_id: str):
    accounts = db.get_customer_accounts(customer_id)
    return replace_none(accounts)

@app.get("/customer/{customer_id}/account/{account_id}")
def get_account_details(customer_id: str, account_id: str):
    account = db.get_account_details(customer_id, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return replace_none(account)

@app.post("/customer/transfer")
def customer_transfer(req: TransferRequest):
    try:
        tx_id = db.transfer_funds(req.from_account, req.to_account, req.amount)
        return replace_none({
            "transaction_id": tx_id, 
            "from_account": req.from_account, 
            "to_account": req.to_account, 
            "amount": req.amount, 
            "status": "completed"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/customer/{customer_id}/transactions")
def get_customer_transactions(customer_id: str):
    transactions = db.get_transaction_history(customer_id)
    return replace_none(transactions)

@app.post("/customer/service-request")
def create_service_request(req: ServiceRequestInput):
    req_id = db.create_service_request(req.customer_id, req.type, req.description)
    return replace_none({
        "request_id": req_id, 
        "customer_id": req.customer_id, 
        "type": req.type, 
        "description": req.description, 
        "status": "pending"
    })

@app.get("/customer/{customer_id}/service-requests")
def get_customer_service_requests(customer_id: str):
    requests = db.get_customer_service_requests(customer_id)
    return replace_none(requests)

@app.post("/admin/customers")
def admin_create_customer(req: AdminCustomerRequest):
    try:
        user_id = db.create_customer(req.name, req.email, req.phone, req.address, hash_password(req.password), "customer")
        return replace_none({"customer_id": user_id, "name": req.name, "email": req.email})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/admin/customers")
def admin_get_customers():
    customers = db.get_all_customers()
    return replace_none(customers)

@app.post("/admin/accounts")
def admin_create_account(req: AdminAccountRequest):
    acc_id = db.create_account(req.customer_id, req.account_type, req.initial_balance)
    return replace_none({
        "account_id": acc_id, 
        "customer_id": req.customer_id, 
        "account_type": req.account_type, 
        "balance": req.initial_balance, 
        "status": "active"
    })

@app.get("/admin/accounts")
def admin_get_accounts():
    accounts = db.get_all_accounts()
    return replace_none(accounts)

@app.get("/admin/transactions")
def admin_get_transactions():
    transactions = db.get_all_transactions()
    return replace_none(transactions)

@app.get("/support/service-requests")
def support_get_service_requests(status: str = ""):
    requests = db.get_service_requests_by_status(status)
    return replace_none(requests)

@app.put("/support/service-requests/{request_id}")
def support_update_request(request_id: str, req: SupportUpdateRequest):
    if req.status not in ["pending", "in-progress", "resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    updated_req = db.update_service_request(request_id, req.status)
    if not updated_req:
        raise HTTPException(status_code=404, detail="Request not found")
    return replace_none(updated_req)
