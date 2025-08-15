from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class AddressSchema(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str

class UserSchema(BaseModel):
    id: str
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = None
    address: Optional[AddressSchema] = None
    date_of_birth: Optional[datetime] = None
    created_at: datetime
    is_active: bool = True
    role: UserRole = UserRole.USER

class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    address: Optional[AddressSchema] = None

class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = None
    address: Optional[AddressSchema] = None
    is_active: Optional[bool] = None

def validate_user_response(response_data: Dict[str, Any]) -> UserSchema:
    """Validate API response against user schema"""
    return UserSchema(**response_data)