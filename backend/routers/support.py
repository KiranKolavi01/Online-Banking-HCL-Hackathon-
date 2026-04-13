from fastapi import APIRouter, HTTPException
from database import db
from models import SupportUpdateRequest, replace_none

router = APIRouter(prefix="/support", tags=["Support"])

@router.get("/service-requests")
def support_get_service_requests(status: str = ""):
    requests = db.get_service_requests_by_status(status)
    return replace_none(requests)

@router.put("/service-requests/{request_id}")
def support_update_request(request_id: str, req: SupportUpdateRequest):
    if req.status not in ["pending", "in-progress", "resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    updated_req = db.update_service_request(request_id, req.status)
    if not updated_req:
        raise HTTPException(status_code=404, detail="Request not found")
    return replace_none(updated_req)
