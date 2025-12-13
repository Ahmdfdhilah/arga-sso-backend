from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer, computed_field
from datetime import datetime

from app.core.utils.file_upload import generate_signed_url_for_path


class ApplicationListItemResponse(BaseModel):
    """Schema for application list items (pagination). Simple."""

    id: UUID = Field(..., description="Application UUID")
    name: str = Field(..., description="Application name")
    code: str = Field(..., description="Application code")
    description: Optional[str] = Field(None, description="Application description")
    base_url: str = Field(..., description="Application base URL")
    is_active: bool = Field(..., description="Is application active")
    single_session: bool = Field(..., description="Single session mode enabled")
    created_at: datetime = Field(..., description="Created timestamp")
    img_path: Optional[str] = Field(None, exclude=True)
    icon_path: Optional[str] = Field(None, exclude=True)

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info):
        return str(v)

    @computed_field
    @property
    def img_url(self) -> Optional[str]:
        """Generate signed URL for application image on-demand"""
        return generate_signed_url_for_path(self.img_path) if self.img_path else None

    @computed_field
    @property
    def icon_url(self) -> Optional[str]:
        """Generate signed URL for application icon on-demand"""
        return generate_signed_url_for_path(self.icon_path) if self.icon_path else None


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
    img_path: Optional[str] = Field(None, exclude=True)
    icon_path: Optional[str] = Field(None, exclude=True)

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info):
        return str(v)

    @computed_field
    @property
    def img_url(self) -> Optional[str]:
        """Generate signed URL for application image on-demand"""
        return generate_signed_url_for_path(self.img_path) if self.img_path else None

    @computed_field
    @property
    def icon_url(self) -> Optional[str]:
        """Generate signed URL for application icon on-demand"""
        return generate_signed_url_for_path(self.icon_path) if self.icon_path else None


class AllowedAppResponse(BaseModel):
    """Full app info for user's allowed applications (my-apps endpoint)."""

    id: UUID = Field(..., description="Application UUID")
    code: str = Field(..., description="Application code")
    name: str = Field(..., description="Application name")
    description: Optional[str] = Field(None, description="Application description")
    base_url: str = Field(..., description="Application base URL")
    is_active: bool = Field(..., description="Is application active")
    img_path: Optional[str] = Field(None, exclude=True)
    icon_path: Optional[str] = Field(None, exclude=True)

    model_config = {"from_attributes": True}

    @field_serializer("id")
    def serialize_id(self, v: UUID, _info):
        return str(v)

    @computed_field
    @property
    def img_url(self) -> Optional[str]:
        """Generate signed URL for application image on-demand"""
        return generate_signed_url_for_path(self.img_path) if self.img_path else None

    @computed_field
    @property
    def icon_url(self) -> Optional[str]:
        """Generate signed URL for application icon on-demand"""
        return generate_signed_url_for_path(self.icon_path) if self.icon_path else None
