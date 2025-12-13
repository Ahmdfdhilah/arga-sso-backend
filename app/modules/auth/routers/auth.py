from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, Query, status
from app.core.schemas import BaseResponse, DataResponse
from app.core.security import get_current_user
from app.modules.auth.dependencies import (
    AuthServiceDep,
    SessionServiceDep,
    EmailAuthServiceDep,
    FirebaseAuthServiceDep,
    OAuth2GoogleServiceDep,
)
from app.modules.auth.schemas import (
    FirebaseLoginRequest,
    EmailPasswordLoginRequest,
    LoginResponse,
    RefreshResponse,
    RefreshTokenRequest,
    UserData,
    SSOTokenExchangeRequest,
)

router = APIRouter()


@router.post(
    "/login/email",
    response_model=DataResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Login dengan email dan password",
)
async def login_with_email(
    request: Request,
    data: EmailPasswordLoginRequest,
    email_auth_service: EmailAuthServiceDep,
) -> DataResponse[LoginResponse]:
    """
    Login dengan email dan password.

    - Jika client_id disediakan: login ke app tertentu, dapat sso_token + access_token
    - Jika client_id null/kosong: SSO-only login, hanya dapat sso_token + allowed_apps
    """
    ip_address = request.client.host if request.client else None
    result = await email_auth_service.login(
        email=data.email,
        password=data.password,
        client_id=data.client_id,
        device_id=data.device_id,
        device_info=data.device_info,
        ip_address=ip_address,
        fcm_token=data.fcm_token,
    )

    if data.client_id:
        return DataResponse(error=False, message="Login berhasil", data=result)
    else:
        return DataResponse(
            error=False,
            message="Login SSO berhasil. Silakan pilih aplikasi.",
            data=result,
        )


@router.post(
    "/login/firebase",
    response_model=DataResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Login dengan Firebase token",
)
async def login_with_firebase(
    request: Request,
    data: FirebaseLoginRequest,
    firebase_auth_service: FirebaseAuthServiceDep,
) -> DataResponse[LoginResponse]:
    ip_address = request.client.host if request.client else None
    result = await firebase_auth_service.login(data, ip_address=ip_address)
    return DataResponse(error=False, message="Login berhasil", data=result)


@router.get(
    "/login/google",
    response_model=DataResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get Google OAuth2 authorization URL",
)
async def get_google_auth_url(
    oauth_service: OAuth2GoogleServiceDep,
    redirect_uri: str = Query(..., description="Redirect URI setelah OAuth"),
    state: Optional[str] = Query(None, description="State parameter untuk security"),
) -> DataResponse[dict]:
    """Generate Google OAuth2 authorization URL."""
    auth_url = oauth_service.get_authorization_url(
        redirect_uri=redirect_uri, state=state
    )
    return DataResponse(
        error=False,
        message="Google OAuth URL berhasil dibuat",
        data={"auth_url": auth_url},
    )


@router.get(
    "/login/google/callback",
    response_model=DataResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Handle Google OAuth2 redirect callback (browser)",
)
async def google_oauth_callback(
    request: Request,
    oauth_service: OAuth2GoogleServiceDep,
    code: str = Query(..., description="Authorization code dari Google"),
    redirect_uri: Optional[str] = Query(
        None, description="Redirect URI yang digunakan saat authorization"
    ),
    client_id: Optional[str] = Query(
        None, description="Application client ID (None for SSO)"
    ),
    device_id: Optional[str] = Query(None, description="Persistent device ID"),
    state: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    fcm_token: Optional[str] = Query(None, description="FCM token"),
    device_info: Optional[str] = Query(None, description="Device info as JSON string"),
) -> DataResponse[LoginResponse]:
    """Handle redirect dari Google. client_id optional untuk SSO-only login."""
    ip_address = request.client.host if request.client else None

    import json as json_module

    parsed_device_info = None
    if device_info:
        try:
            parsed_device_info = json_module.loads(device_info)
        except:
            pass

    result = await oauth_service.handle_callback(
        code=code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        device_id=device_id,
        device_info=parsed_device_info,
        ip_address=ip_address,
        fcm_token=fcm_token,
    )
    return DataResponse(error=False, message="Login berhasil", data=result)


@router.post(
    "/exchange",
    response_model=DataResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    summary="Exchange SSO token untuk mendapat token aplikasi lain",
)
async def exchange_sso_token(
    request: Request,
    data: SSOTokenExchangeRequest,
    auth_service: AuthServiceDep,
) -> DataResponse[LoginResponse]:
    """
    Exchange SSO session token untuk mendapat access_token dan refresh_token
    untuk aplikasi lain tanpa harus login ulang.

    Flow:
    1. User login ke app A → dapat sso_token
    2. User buka app B → call /exchange dengan sso_token + client_id app B
    3. User dapat tokens untuk app B tanpa login lagi
    """
    ip_address = request.client.host if request.client else None
    result = await auth_service.exchange_sso_token(
        sso_token=data.sso_token,
        client_id=data.client_id,
        device_id=data.device_id,
        device_info=data.device_info,
        ip_address=ip_address,
        fcm_token=data.fcm_token,
    )
    return DataResponse(
        error=False,
        message=f"Token exchange berhasil untuk aplikasi {data.client_id}",
        data=result,
    )


@router.post(
    "/refresh",
    response_model=DataResponse[RefreshResponse],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthServiceDep,
) -> DataResponse[RefreshResponse]:
    """Refresh access token menggunakan refresh token dan device_id."""
    result = await auth_service.refresh_token(
        data.refresh_token, device_id=data.device_id
    )
    return DataResponse(error=False, message="Token berhasil diperbarui", data=result)


@router.post(
    "/logout/client",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout dari aplikasi tertentu (client-specific)",
)
async def logout_from_client(
    auth_service: AuthServiceDep,
    current_user: UserData = Depends(get_current_user),
    x_client_id: str = Header(
        ..., alias="X-Client-ID", description="Application client ID"
    ),
    x_device_id: Optional[str] = Header(
        None, alias="X-Device-ID", description="Device ID (optional)"
    ),
) -> BaseResponse:
    """
    Logout dari aplikasi tertentu:
    - Jika X-Device-ID provided: logout device itu saja untuk client ini
    - Jika X-Device-ID tidak ada: logout semua device untuk client ini
    """
    if x_device_id:
        await auth_service.logout_client_device(
            current_user.id, x_client_id, x_device_id
        )
        return BaseResponse(
            error=False,
            message=f"Logout dari {x_client_id} (device {x_device_id}) berhasil",
        )
    else:
        await auth_service.logout_client(current_user.id, x_client_id)
        return BaseResponse(
            error=False, message=f"Logout dari semua device {x_client_id} berhasil"
        )


@router.post(
    "/logout",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Global logout (semua aplikasi dan device)",
)
async def logout_global(
    auth_service: AuthServiceDep,
    current_user: UserData = Depends(get_current_user),
) -> BaseResponse:
    """Logout dari SEMUA aplikasi dan SEMUA device"""
    await auth_service.logout_all(current_user.id)
    return BaseResponse(error=False, message="Logout dari semua aplikasi berhasil")


@router.post(
    "/logout/sso",
    response_model=BaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout SSO session saja (tanpa logout dari aplikasi)",
)
async def logout_sso(
    auth_service: AuthServiceDep,
    current_user: UserData = Depends(get_current_user),
) -> BaseResponse:
    """
    Logout dari SSO session saja.
    Endpoint ini untuk SSO frontend yang tidak terdaftar sebagai client.
    Session di aplikasi lain tetap aktif.
    """
    await auth_service.logout_sso(current_user.id)
    return BaseResponse(error=False, message="Logout SSO berhasil")


@router.post(
    "/validate",
    response_model=DataResponse[UserData],
    status_code=status.HTTP_200_OK,
    summary="Validate access token (untuk backend services)",
)
async def validate_token(
    current_user: UserData = Depends(get_current_user),
) -> DataResponse[UserData]:
    """
    Validate JWT access token dan return user data.
    Endpoint ini untuk backend services yang perlu verify token.

    Usage:
    POST /api/v1/auth/validate
    Authorization: Bearer <access_token>
    """
    return DataResponse(
        error=False,
        message="Token valid",
        data=current_user,
    )


@router.get(
    "/sessions",
    response_model=DataResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Lihat semua sesi aktif (grouped by client)",
)
async def list_sessions(
    session_service: SessionServiceDep,
    current_user: UserData = Depends(get_current_user),
) -> DataResponse[dict]:
    """
    Returns sessions grouped by client_id:
    {
        "sessions": {
            "hris_web": [
                {"device_id": "...", "device_info": {...}, ...}
            ],
            "hris_mobile": [...]
        },
        "total_clients": 2,
        "total_sessions": 3
    }
    """
    all_sessions = await session_service.get_all_sessions(current_user.id)

    # Group by client_id
    grouped = {}
    for session in all_sessions:
        client_id = session.get("client_id", "unknown")
        if client_id not in grouped:
            grouped[client_id] = []
        grouped[client_id].append(
            {
                "device_id": session["device_id"],
                "device_info": session.get("device_info"),
                "ip_address": session.get("ip_address"),
                "created_at": session["created_at"],
                "last_activity": session["last_activity"],
            }
        )

    return DataResponse(
        error=False,
        message=f"Ditemukan {len(all_sessions)} sesi aktif di {len(grouped)} aplikasi",
        data={
            "sessions": grouped,
            "total_clients": len(grouped),
            "total_sessions": len(all_sessions),
        },
    )
