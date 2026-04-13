import bcrypt
from fastapi import APIRouter, HTTPException
from database import db
from models import SignupRequest, SigninRequest, replace_none

# Initialize the router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["Auth"])

def hash_password(password: str) -> str:
    # Hashes password with bcrypt using a randomly generated salt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    # Verifies if the provided plain-text password matches the stored bcrypt hash
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

@router.post("/signup")
def auth_signup(req: SignupRequest):
    # Registration endpoint for creating a new user account
    
    # 1. Validate password length
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # 2. Validate phone number format
    if not req.phone.isdigit() or len(req.phone) != 10:
        raise HTTPException(status_code=400, detail="Phone number must be exactly 10 digits")
        
    # 3. Restrict registration to customers only for security
    if req.role != 'customer':
        raise HTTPException(status_code=403, detail="Unauthorized role selected for public registration. Only customers can register.")
        
    try:
        # Create the customer record in the database
        user_id = db.create_customer(req.name, req.email, req.phone, req.address, hash_password(req.password), req.role)
        return replace_none({"user_id": user_id, "name": req.name, "role": req.role})
    except ValueError as e:
        # Catch duplicate emails or other DB validations
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/signin")
def auth_signin(req: SigninRequest):
    # Authentication endpoint for logging in
    
    # First, lookup the user in the customers table
    row = db.get_customer_by_email(req.email)
    
    if row:
        user_id = row["customer_id"]
        role = row["role"]
        pwd_hash = row["password_hash"]
        name = row["name"]
    else:
        # If not found, lookup the user in the bank_staff table
        row = db.get_staff_by_email(req.email)
        if row:
            user_id = row["staff_id"]
            role = row["role"]
            pwd_hash = row["password_hash"]
            name = ""
        else:
            raise HTTPException(status_code=401, detail="Wrong credentials")
            
    # Verify the password hash
    if not check_password(req.password, pwd_hash):
        raise HTTPException(status_code=401, detail="Wrong credentials")
        
    # Return user details for session persistence
    return replace_none({"user_id": user_id, "name": name, "role": role})
