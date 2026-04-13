import bcrypt
from fastapi import APIRouter, HTTPException
from database import db
from models import SignupRequest, SigninRequest, replace_none

router = APIRouter(prefix="/auth", tags=["Auth"])

def hash_password(password: str) -> str:
    # Hashes password with bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    # Verifies credentials
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

@router.post("/signup")
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

@router.post("/signin")
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
