from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ------------------- Auth -------------------

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ------------------- User -------------------

class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    phone: Optional[str] = None
    role_id: Optional[int] = None
    company_id: Optional[int] = None
    view_type: str = "web"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    view_type: Optional[str] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    view_type: str
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ------------------- Role -------------------

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permissions: list["PermissionCreate"] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleRead(RoleBase):
    id: int
    is_active: bool
    created_at: datetime
    permissions: list["PermissionRead"] = []

    model_config = {"from_attributes": True}


# ------------------- Permission -------------------

class PermissionCreate(BaseModel):
    module: str
    action: str  # read, create, update, delete, review, correct, approve, reject, send_sap
    scope_type: str = "all"
    scope_id: Optional[int] = None


class PermissionRead(PermissionCreate):
    id: int

    model_config = {"from_attributes": True}
