from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer, computed_field
from datetime import datetime

from app.core.enums import UserRole, UserStatus
from app.modules.auth.schemas.responses import AllowedApp
from app.core.utils.file_upload import generate_signed_url_for_path


class UserListItemResponse(BaseModel):
    """Schema for user list items (pagination). Simple, no joins."""

    id: UUID = Field(..., description="User UUID")
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_path: Optional[str] = Field(None, exclude=True)
    status: UserStatus
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info):
        return str(v)

    @computed_field
    @property
    def avatar_url(self) -> Optional[str]:
        """Generate signed URL for avatar on-demand"""
        return generate_signed_url_for_path(self.avatar_path) if self.avatar_path else None


class UserResponse(BaseModel):
    """Schema for user detail (get by id). Includes joined data."""

    id: UUID = Field(..., description="User UUID")
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_path: Optional[str] = Field(None, exclude=True)
    status: UserStatus
    role: UserRole
    created_at: datetime
    updated_at: datetime
    allowed_apps: List[AllowedApp] = Field(
        default_factory=list, description="User's allowed applications"
    )

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info):
        return str(v)

    @computed_field
    @property
    def avatar_url(self) -> Optional[str]:
        """Generate signed URL for avatar on-demand"""
        return generate_signed_url_for_path(self.avatar_path) if self.avatar_path else None
