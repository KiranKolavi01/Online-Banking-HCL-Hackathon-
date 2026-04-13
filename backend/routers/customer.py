from fastapi import APIRouter, HTTPException
from database import db
from models import TransferRequest, ServiceRequestInput, replace_none

router = APIRouter(prefix="/customer", tags=["Customer"])

@router.get("/{customer_id}/accounts")
def get_customer_accounts(customer_id: int):
    accounts = db.get_customer_accounts(customer_id)
    return replace_none(accounts)

@router.get("/{customer_id}/account/{account_id}")
def get_account_details(customer_id: int, account_id: str):
    account = db.get_account_details(customer_id, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return replace_none(account)

@router.post("/transfer")
def customer_transfer(req: TransferRequest):
    try:
        # Security Gateway: Verify the sender account genuinely belongs to the current logged-in customer
        sender_account = db.get_account_details(req.customer_id, req.from_account)
        if not sender_account:
            raise HTTPException(status_code=403, detail="Unauthorized: You do not own the sender account")
            
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

@router.get("/{customer_id}/transactions")
def get_customer_transactions(customer_id: int):
    transactions = db.get_transaction_history(customer_id)
    return replace_none(transactions)

@router.post("/service-request")
def create_service_request(req: ServiceRequestInput):
    req_id = db.create_service_request(req.customer_id, req.type, req.description)
    return replace_none({
        "request_id": req_id, 
        "customer_id": req.customer_id, 
        "type": req.type, 
        "description": req.description, 
        "status": "pending"
    })

@router.get("/{customer_id}/service-requests")
def get_customer_service_requests(customer_id: int):
    requests = db.get_customer_service_requests(customer_id)
    return replace_none(requests)
