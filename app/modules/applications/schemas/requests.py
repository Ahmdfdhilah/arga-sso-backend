from typing import Optional
from pydantic import BaseModel, Field


class ApplicationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9_-]+$")
    description: Optional[str] = None
    base_url: str = Field(..., min_length=1, max_length=500)
    single_session: bool = Field(
        default=False,
        description="If True, only 1 session allowed per device for this app"
    )


class ApplicationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    code: Optional[str] = Field(
        None, min_length=2, max_length=100, pattern=r"^[a-z0-9_-]+$"
    )
    description: Optional[str] = None
    base_url: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None
    single_session: Optional[bool] = Field(
        None,
        description="If True, only 1 session allowed per device for this app"
    )


class UserApplicationAssignRequest(BaseModel):
    application_ids: list[str] = Field(
        ..., description="List of application UUIDs to assign"
    )
