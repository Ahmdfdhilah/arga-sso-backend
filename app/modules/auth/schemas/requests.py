from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class FirebaseLoginRequest(BaseModel):
    firebase_token: str = Field(..., min_length=1, description="Firebase ID token")
    client_id: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Application client ID (code). If null, SSO-only login.",
    )
    device_id: Optional[str] = Field(
        None, description="Persistent device ID. If provided, reuses existing session for this device."
    )
    fcm_token: Optional[str] = Field(
        None, description="FCM token for push notifications"
    )
    device_info: Optional[Dict[str, Any]] = Field(
        None, description="Device information"
    )


class EmailPasswordLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    client_id: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Application client ID (code). If null, SSO-only login.",
    )
    device_id: Optional[str] = Field(
        None, description="Persistent device ID. If provided, reuses existing session for this device."
    )
    fcm_token: Optional[str] = Field(
        None, description="FCM token for push notifications"
    )
    device_info: Optional[Dict[str, Any]] = Field(
        None, description="Device information"
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="JWT refresh token")
    device_id: str = Field(..., min_length=1, description="Device ID from login")


class LogoutRequest(BaseModel):
    device_id: Optional[str] = Field(
        None, description="Device ID to logout. If None, logout all devices"
    )


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="User name")
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="Password for email auth")
    phone: Optional[str] = Field(
        None, pattern=r"^\+?[0-9]{10,15}$", description="Phone number"
    )


class OAuth2GoogleCallbackRequest(BaseModel):
    code: str = Field(..., min_length=1, description="Authorization code dari Google")
    client_id: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Application client ID (code). If null, SSO-only login.",
    )
    device_id: Optional[str] = Field(
        None, description="Persistent device ID. If provided, reuses existing session for this device."
    )
    state: Optional[str] = Field(None, description="State parameter untuk security")
    fcm_token: Optional[str] = Field(
        None, description="FCM token for push notifications"
    )
    device_info: Optional[Dict[str, Any]] = Field(
        None, description="Device information"
    )


class SSOTokenExchangeRequest(BaseModel):
    """Request untuk exchange SSO token ke app-specific tokens."""

    sso_token: str = Field(..., min_length=1, description="Global SSO session token")
    client_id: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Application client ID (code) to get tokens for",
    )
    device_id: Optional[str] = Field(
        None, description="Persistent device ID. If provided, reuses existing session for this device."
    )
    fcm_token: Optional[str] = Field(
        None, description="FCM token for push notifications"
    )
    device_info: Optional[Dict[str, Any]] = Field(
        None, description="Device information"
    )
