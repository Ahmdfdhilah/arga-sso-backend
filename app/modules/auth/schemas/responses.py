from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class AllowedApp(BaseModel):
    """Minimal app info for allowed apps list."""

    id: str = Field(..., description="Application UUID")
    code: str = Field(..., description="Application code")
    name: str = Field(..., description="Application name")
    base_url: Optional[str] = Field(None, description="Application base URL")
    
class UserData(BaseModel):
    id: str = Field(..., description="User ID")
    role: str = Field(..., description="User role")
    name: Optional[str] = Field(None, description="User name")
    email: Optional[str] = Field(None, description="User email")
    avatar_url: Optional[str] = Field(None, description="User avatar URL")
    allowed_apps: List[AllowedApp] = Field(
        default_factory=list, description="Allowed applications"
    )


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class LoginResponse(BaseModel):
    """
    Unified login response.

    - sso_token: Always present
    - access_token/refresh_token: Present if client_id was provided
    - device_id: Present if client_id was provided (save this for future logins)
    """

    sso_token: str = Field(
        ..., description="Global SSO session token for token exchange"
    )
    access_token: Optional[str] = Field(
        None, description="JWT access token (present if client_id provided)"
    )
    refresh_token: Optional[str] = Field(
        None, description="JWT refresh token (present if client_id provided)"
    )
    device_id: Optional[str] = Field(
        None, description="Device ID for this session (save and reuse for future logins)"
    )
    token_type: str = Field("bearer", description="Token type")
    expires_in: Optional[int] = Field(
        None, description="Token expiry in seconds (present if client_id provided)"
    )
    user: UserData = Field(..., description="User data")


class RefreshResponse(BaseModel):
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class SessionInfo(BaseModel):
    device_id: str = Field(..., description="Device ID")
    device_info: Optional[dict] = Field(None, description="Device information")
    ip_address: Optional[str] = Field(None, description="IP address")
    created_at: datetime = Field(..., description="Session created at")
    last_activity: datetime = Field(..., description="Last activity time")


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo] = Field(
        default_factory=list, description="Active sessions"
    )
    total: int = Field(..., description="Total sessions count")
