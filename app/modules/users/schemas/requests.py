from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

from app.core.enums import UserRole, UserStatus


class UserCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    avatar_path: Optional[str] = None
    role: UserRole = Field(default=UserRole.USER)
    status: UserStatus = Field(default=UserStatus.ACTIVE)


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    avatar_path: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
