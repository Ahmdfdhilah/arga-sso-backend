"""Use case untuk exchange SSO token menjadi app-specific tokens."""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

from app.core.exceptions import (
    UnauthorizedException,
    NotFoundException,
    ForbiddenException,
)
from app.modules.auth.schemas import LoginResponse
from app.modules.auth.utils.token_helper import TokenHelper
from app.modules.users.repositories import UserQueries
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService
    from app.modules.auth.services.sso_session_service import SSOSessionService

logger = logging.getLogger(__name__)


class ExchangeSSOTokenUseCase:
    """Use case untuk exchange SSO token menjadi app-specific access dan refresh tokens."""

    def __init__(
        self,
        user_queries: UserQueries,
        session_service: "SessionService",
        sso_session_service: "SSOSessionService",
        app_queries: ApplicationQueries,
    ):
        self.user_queries = user_queries
        self.session_service = session_service
        self.sso_session_service = sso_session_service
        self.app_queries = app_queries
        self.token_helper = TokenHelper(session_service, sso_session_service)

    async def execute(
        self,
        sso_token: str,
        client_id: str,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """
        Exchange SSO token untuk app-specific tokens.

        Args:
            sso_token: SSO token yang diperoleh saat login
            client_id: Application client code
            device_id: Optional device identifier
            device_info: Optional device metadata
            ip_address: Optional IP address
            fcm_token: Optional FCM token untuk push notification

        Returns:
            LoginResponse dengan access token, refresh token, dan user data

        Raises:
            UnauthorizedException: SSO token tidak valid atau expired
            NotFoundException: User atau aplikasi tidak ditemukan
            ForbiddenException: User tidak memiliki akses ke aplikasi
        """
        logger.info(f"SSO token exchange untuk client: {client_id}")

        # Validasi SSO token
        sso_session = await self.sso_session_service.validate_sso_token(sso_token)
        if not sso_session:
            raise UnauthorizedException("SSO session tidak valid atau sudah expired")

        # Validasi user exists
        user_id = sso_session["user_id"]
        user = await self.user_queries.get_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan")

        # Validasi aplikasi exists dan aktif
        app = await self.app_queries.get_by_code(client_id)
        if not app or not app.is_active:
            raise NotFoundException(
                f"Aplikasi '{client_id}' tidak ditemukan atau tidak aktif"
            )

        # Validasi user memiliki akses ke aplikasi
        user_apps = await self.app_queries.get_user_applications(user_id)
        if str(app.id) not in [str(a.id) for a in user_apps]:
            raise ForbiddenException(
                f"User tidak memiliki akses ke aplikasi '{client_id}'"
            )

        logger.info(f"Token exchange successful: {user_id} -> {client_id}")

        # Generate app-specific tokens dan create session
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
