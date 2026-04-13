from fastapi import APIRouter, HTTPException
from database import db
from auth import hash_password
from models import AdminCustomerRequest, AdminAccountRequest, replace_none

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/customers")
def admin_create_customer(req: AdminCustomerRequest):
    if not req.phone.isdigit() or len(req.phone) != 10:
        raise HTTPException(status_code=400, detail="Phone number must be exactly 10 digits")
        
    try:
        user_id = db.create_customer(req.name, req.email, req.phone, req.address, hash_password(req.password), "customer")
        return replace_none({"customer_id": user_id, "name": req.name, "email": req.email})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/customers")
def admin_get_customers():
    customers = db.get_all_customers()
    return replace_none(customers)

@router.post("/accounts")
def admin_create_account(req: AdminAccountRequest):
    try:
        conn = db.get_connection()
        cursor = conn.execute("SELECT customer_id FROM customers WHERE customer_id = ?", (req.customer_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Customer does not exist")
        conn.close()
        
        acc_id = db.create_account(req.customer_id, req.account_type, req.balance)
        return replace_none({
            "account_id": acc_id, 
            "customer_id": req.customer_id, 
            "account_type": req.account_type, 
            "balance": req.balance, 
            "status": "active"
        })
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Internal error or bad input")

@router.get("/accounts")
def admin_get_accounts():
    accounts = db.get_all_accounts()
    return replace_none(accounts)

@router.get("/transactions")
def admin_get_transactions():
    transactions = db.get_all_transactions()
    return replace_none(transactions)
