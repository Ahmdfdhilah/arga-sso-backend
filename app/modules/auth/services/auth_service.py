import logging
from typing import Optional, Dict, Any

from app.config.settings import settings
from app.core.security import TokenService
from app.core.exceptions import (
    UnauthorizedException,
    NotFoundException,
    ForbiddenException,
)
from app.modules.auth.services.session_service import SessionService
from app.modules.auth.services.sso_session_service import SSOSessionService
from app.modules.auth.schemas import RefreshResponse, UserData, LoginResponse
from app.modules.auth.schemas.responses import AllowedApp
from app.modules.auth.utils.token_helper import TokenHelper
from app.modules.users.repositories import UserQueries
from app.modules.auth.repositories import AuthProviderQueries
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        user_queries: UserQueries,
        auth_queries: AuthProviderQueries,
        session_service: SessionService,
        sso_session_service: SSOSessionService,
        app_queries: ApplicationQueries,
    ):
        self.user_queries = user_queries
        self.auth_queries = auth_queries
        self.session_service = session_service
        self.sso_session_service = sso_session_service
        self.app_queries = app_queries
        self.token_helper = TokenHelper(session_service, sso_session_service)

    async def exchange_sso_token(
        self,
        sso_token: str,
        client_id: str,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """Exchange SSO token for app-specific tokens."""
        logger.info(f"SSO token exchange for client: {client_id}")

        sso_session = await self.sso_session_service.validate_sso_token(sso_token)
        if not sso_session:
            raise UnauthorizedException("SSO session tidak valid atau sudah expired")

        user_id = sso_session["user_id"]
        user = await self.user_queries.get_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan")

        app = await self.app_queries.get_by_code(client_id)
        if not app or not app.is_active:
            raise NotFoundException(
                f"Aplikasi '{client_id}' tidak ditemukan atau tidak aktif"
            )

        user_apps = await self.app_queries.get_user_applications(user_id)
        if str(app.id) not in [str(a.id) for a in user_apps]:
            raise ForbiddenException(
                f"User tidak memiliki akses ke aplikasi '{client_id}'"
            )

        logger.info(f"Token exchange successful: {user_id} -> {client_id}")

        return await self.token_helper.create_app_tokens_for_exchange(
            user=user,
            client_id=client_id,
            sso_token=sso_token,
            single_session=app.single_session,
            device_id=device_id,
            device_info=device_info,
            ip_address=ip_address,
            fcm_token=fcm_token,
        )

    async def refresh_token(
        self,
        refresh_token: str,
        device_id: str,
    ) -> RefreshResponse:
        """
        Refresh access token using refresh token.
        Validates client_id and device_id from token payload.
        """
        logger.info("Token refresh attempt")

        payload = TokenService.verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        client_id = payload.get("client_id") or "sso_portal" 
        token_device_id = payload.get("device_id")

        if not user_id or not isinstance(user_id, str):
            raise UnauthorizedException("Invalid token payload: missing user_id")

        if token_device_id and token_device_id != device_id:
            raise UnauthorizedException("Device ID mismatch")

        if not await self.session_service.validate_refresh_token(
            user_id=user_id,
            client_id=client_id,
            device_id=device_id,
            refresh_token=refresh_token,
        ):
            raise UnauthorizedException("Invalid refresh token or session expired")

        user = await self.user_queries.get_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan")

        allowed_apps, allowed_app_codes = TokenHelper.extract_allowed_apps_from_user(
            user
        )

        from app.core.utils.file_upload import generate_signed_url_for_path
        avatar_url = generate_signed_url_for_path(user.avatar_path) if user.avatar_path else None

        new_access_token = TokenService.create_access_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            email=user.email,
            avatar_url=avatar_url,
            extra_claims={
                "allowed_apps": allowed_app_codes,
                "client_id": client_id,
            },
        )
        new_refresh_token = TokenService.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            client_id=client_id,
            device_id=device_id,
        )

        await self.session_service.update_session(
            user_id=user_id,
            client_id=client_id,
            device_id=device_id,
            refresh_token=new_refresh_token,
        )

        logger.info(
            f"Token refreshed for user {user_id}, client {client_id}, "
            f"device {device_id} with {len(allowed_apps)} allowed apps"
        )

        return RefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, user_id: str, device_id: Optional[str] = None) -> None:
        """
        Global logout - logout from all clients and devices.
        DEPRECATED: Use logout_all instead.
        """
        logger.info(f"Global logout attempt for user {user_id}")
        await self.session_service.delete_all_sessions(user_id)
        logger.info(f"User {user_id} logged out from all clients and devices")

    async def logout_all(self, user_id: str) -> None:
        """Logout from all clients and all devices."""
        logger.info(f"Logout all attempt for user {user_id}")
        await self.session_service.delete_all_sessions(user_id)
        await self.sso_session_service.delete_sso_session(user_id)
        logger.info(f"User {user_id} logged out from all clients and devices")

    async def logout_sso(self, user_id: str) -> None:
        """
        Logout SSO session only.
        This invalidates the SSO token but keeps app sessions active.
        Used by SSO frontend which is not a registered client.
        """
        logger.info(f"SSO logout attempt for user {user_id}")
        await self.sso_session_service.delete_sso_session(user_id)
        await self.session_service.delete_client_sessions(user_id, "sso_portal")
        logger.info(f"User {user_id} SSO session deleted")

    async def logout_client(self, user_id: str, client_id: str) -> None:
        """Logout from specific client (all devices for that client)."""
        logger.info(f"Client logout attempt for user {user_id}, client {client_id}")
        
        await self.session_service.delete_client_sessions(user_id, client_id)
        logger.info(f"User {user_id} logged out from client {client_id} (all devices)")

    async def logout_client_device(
        self, user_id: str, client_id: str, device_id: str
    ) -> None:
        """Logout from specific device for specific client."""
        logger.info(
            f"Client device logout for user {user_id}, "
            f"client {client_id}, device {device_id}"
        )       
        await self.session_service.delete_client_device_session(
            user_id, client_id, device_id
        )
        logger.info(
            f"User {user_id} logged out from client {client_id}, device {device_id}"
        )

    async def verify_access_token(self, access_token: str) -> UserData:
        payload = TokenService.verify_token(access_token, token_type="access")

        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not isinstance(user_id, str):
            raise UnauthorizedException("Invalid token payload: missing user id")
        if not role or not isinstance(role, str):
            raise UnauthorizedException("Invalid token payload: missing role")

        # Extract allowed_apps from payload
        allowed_app_codes = payload.get("allowed_apps", [])
        allowed_apps = [
            AllowedApp(id="", code=code, name="") for code in allowed_app_codes
        ]

        return UserData(
            id=user_id,
            role=role,
            name=payload.get("name"),
            email=payload.get("email"),
            allowed_apps=allowed_apps,
        )
