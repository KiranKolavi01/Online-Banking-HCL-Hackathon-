"""
Pydantic Models
This file defines the data structures and validation rules for all incoming API requests.
FastAPI uses these models to automatically validate request bodies and return 422 errors for bad data.
"""
from pydantic import BaseModel, StrictInt, validator
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
    customer_id: int
    from_account: str
    to_account: str
    amount: float

class ServiceRequestInput(BaseModel):
    customer_id: int
    type: str
    description: str

class AdminCustomerRequest(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    password: str

class AdminAccountRequest(BaseModel):
    customer_id: int
    account_type: str
    balance: float

    class Config:
        extra = "forbid"

    @validator("account_type", pre=True)
    def to_lower_and_validate(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if v not in ["savings", "current"]:
                raise ValueError("Invalid account type")
        return v

    @validator("balance")
    def validate_balance(cls, v):
        if v < 0:
            raise ValueError("Invalid balance value")
        return v

class SupportUpdateRequest(BaseModel):
    status: str

def replace_none(data):
    # Recursively replaces None values with empty strings to ensure frontend table compatibility
    if isinstance(data, dict):
        return {k: ("" if v is None else replace_none(v)) for k, v in data.items()}
    elif isinstance(data, list):
        return [replace_none(item) for item in data]
    return data
