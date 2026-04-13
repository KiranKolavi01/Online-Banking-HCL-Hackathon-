from pydantic import BaseModel
from typing import Optional

class SignupRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    password: str
    role: str

class SigninRequest(BaseModel):
    email: str
    password: str

class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float

class ServiceRequestInput(BaseModel):
    customer_id: str
    type: str
    description: str

class AdminCustomerRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    password: str

class AdminAccountRequest(BaseModel):
    customer_id: str
    account_type: str
    initial_balance: float

class SupportUpdateRequest(BaseModel):
    status: str
