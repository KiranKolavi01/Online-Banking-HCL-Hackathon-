"""
Support Routes
Provides limited endpoints specifically for the Support role to view and
resolve service requests submitted by customers across the system.
"""
from fastapi import APIRouter, HTTPException
from database import db
from models import SupportUpdateRequest, replace_none

router = APIRouter(prefix="/support", tags=["Support"])

@router.get("/service-requests")
def support_get_service_requests(status: str = ""):
    # Allows support staff to fetch tickets, optionally filtering by ticket status
    requests = db.get_service_requests_by_status(status)
    return replace_none(requests)

@router.put("/service-requests/{request_id}")
def support_update_request(request_id: str, req: SupportUpdateRequest):
    # Update the status (e.g. pending -> resolved) of an existing service request
    if req.status not in ["pending", "in-progress", "resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    updated_req = db.update_service_request(request_id, req.status)
    if not updated_req:
        raise HTTPException(status_code=404, detail="Request not found")
    return replace_none(updated_req)
