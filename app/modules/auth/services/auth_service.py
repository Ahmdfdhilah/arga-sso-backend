"""Auth service facade - orchestrates authentication use cases."""

import logging
from typing import Optional, Dict, Any

from app.modules.auth.services.session_service import SessionService
from app.modules.auth.services.sso_session_service import SSOSessionService
from app.modules.auth.schemas import RefreshResponse, UserData, LoginResponse
from app.modules.users.repositories import UserQueries
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)
from app.modules.auth.use_cases.token.exchange_sso_token import (
    ExchangeSSOTokenUseCase,
)
from app.modules.auth.use_cases.token.refresh_token import RefreshTokenUseCase
from app.modules.auth.use_cases.token.verify_access_token import (
    VerifyAccessTokenUseCase,
)
from app.modules.auth.use_cases.logout.logout_all import LogoutAllUseCase
from app.modules.auth.use_cases.logout.logout_sso import LogoutSSOUseCase
from app.modules.auth.use_cases.logout.logout_client import LogoutClientUseCase
from app.modules.auth.use_cases.logout.logout_client_device import (
    LogoutClientDeviceUseCase,
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Auth service facade.
    Mengkoordinasikan use cases untuk authentication dan token management.
    """

    def __init__(
        self,
        user_queries: UserQueries,
        session_service: SessionService,
        sso_session_service: SSOSessionService,
        app_queries: ApplicationQueries,
    ):
        self.exchange_sso_token_uc = ExchangeSSOTokenUseCase(
            user_queries, session_service, sso_session_service, app_queries
        )
        self.refresh_token_uc = RefreshTokenUseCase(user_queries, session_service)
        self.verify_access_token_uc = VerifyAccessTokenUseCase()
        self.logout_all_uc = LogoutAllUseCase(session_service, sso_session_service)
        self.logout_sso_uc = LogoutSSOUseCase(session_service, sso_session_service)
        self.logout_client_uc = LogoutClientUseCase(session_service)
        self.logout_client_device_uc = LogoutClientDeviceUseCase(session_service)

    async def exchange_sso_token(
        self,
        sso_token: str,
        client_id: str,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """Exchange SSO token untuk app-specific tokens."""
        return await self.exchange_sso_token_uc.execute(
            sso_token=sso_token,
            client_id=client_id,
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
        """Refresh access token menggunakan refresh token."""
        return await self.refresh_token_uc.execute(
            refresh_token=refresh_token,
            device_id=device_id,
        )

    async def logout_all(self, user_id: str) -> None:
        """Logout dari semua clients dan semua devices."""
        await self.logout_all_uc.execute(user_id)

    async def logout_sso(self, user_id: str) -> None:
        """Logout SSO session saja, tidak menghapus app sessions."""
        await self.logout_sso_uc.execute(user_id)

    async def logout_client(self, user_id: str, client_id: str) -> None:
        """Logout dari specific client (semua devices)."""
        await self.logout_client_uc.execute(user_id, client_id)

    async def logout_client_device(
        self, user_id: str, client_id: str, device_id: str
    ) -> None:
        """Logout dari specific device di specific client."""
        await self.logout_client_device_uc.execute(user_id, client_id, device_id)

    async def verify_access_token(self, access_token: str) -> UserData:
        """Verify access token dan extract user data."""
        return await self.verify_access_token_uc.execute(access_token)
