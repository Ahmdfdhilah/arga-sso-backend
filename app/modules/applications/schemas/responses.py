from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime


class ApplicationListItemResponse(BaseModel):
    """Schema for application list items (pagination). Simple."""

    id: UUID = Field(..., description="Application UUID")
    name: str = Field(..., description="Application name")
    code: str = Field(..., description="Application code")
    is_active: bool = Field(..., description="Is application active")
    single_session: bool = Field(..., description="Single session mode enabled")
    created_at: datetime = Field(..., description="Created timestamp")

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info):
        return str(v)


class ApplicationResponse(BaseModel):
    """Schema for application detail (get by id). Full info."""

    id: UUID = Field(..., description="Application UUID")
    name: str = Field(..., description="Application name")
    code: str = Field(..., description="Application code (unique identifier)")
    description: Optional[str] = Field(None, description="Application description")
    base_url: str = Field(..., description="Application base URL")
    is_active: bool = Field(..., description="Is application active")
    single_session: bool = Field(
        ...,
        description="If True, only 1 session allowed per device for this app"
    )
    created_at: datetime = Field(..., description="Created timestamp")
    updated_at: datetime = Field(..., description="Updated timestamp")

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info):
        return str(v)


class AllowedAppResponse(BaseModel):
    """Minimal app info for allowed apps in token/response."""

    id: str = Field(..., description="Application UUID")
    code: str = Field(..., description="Application code")
    name: str = Field(..., description="Application name")
