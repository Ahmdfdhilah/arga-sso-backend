"""Use case untuk handle Google OAuth2 callback dengan auto provider linking."""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

from app.core.security import OAuth2GoogleSecurityService
from app.core.exceptions import UnauthorizedException
from app.core.enums import AuthProvider
from app.modules.auth.repositories import AuthProviderQueries, AuthProviderCommands
from app.modules.auth.utils.token_helper import TokenHelper
from app.modules.auth.utils.client_validator import ClientValidator
from app.modules.auth.schemas import LoginResponse
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.auth.utils.avatar_helper import download_and_upload_avatar_from_url
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService
    from app.modules.auth.services.sso_session_service import SSOSessionService

logger = logging.getLogger(__name__)


class GoogleOAuthHandleCallbackUseCase:
    """Use case untuk handle OAuth2 Google callback dengan auto provider linking."""

    def __init__(
        self,
        auth_queries: AuthProviderQueries,
        auth_commands: AuthProviderCommands,
        user_queries: UserQueries,
        user_commands: UserCommands,
        session_service: "SessionService",
        sso_session_service: "SSOSessionService",
        app_queries: ApplicationQueries,
    ):
        self.auth_queries = auth_queries
        self.auth_commands = auth_commands
        self.user_queries = user_queries
        self.user_commands = user_commands
        self.session_service = session_service
        self.sso_session_service = sso_session_service
        self.app_queries = app_queries
        self.token_helper = TokenHelper(session_service, sso_session_service)
        self.client_validator = ClientValidator(app_queries)

    async def execute(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
        client_id: Optional[str] = None,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """
        Handle OAuth2 Google callback.
        Otomatis link provider jika user sudah terdaftar tapi belum punya Google provider.

        Args:
            code: Authorization code dari Google
            redirect_uri: Redirect URI yang sama dengan saat request authorization
            client_id: Optional application client code
            device_id: Optional device identifier
            device_info: Optional device metadata
            ip_address: Optional IP address
            fcm_token: Optional FCM token untuk push notification

        Returns:
            LoginResponse dengan tokens dan user data

        Raises:
            UnauthorizedException: User tidak terdaftar dalam sistem
        """
        # Verify code dan get user data dari Google
        google_user = await OAuth2GoogleSecurityService.verify_and_get_user(
            code, redirect_uri
        )

        # Cek apakah sudah ada auth provider
        auth_provider = await self.auth_queries.get_by_provider_user_id(
            provider=AuthProvider.GOOGLE.value,
            provider_user_id=google_user.google_id,
        )

        if auth_provider:
            # Provider sudah ada, ambil user
            user = auth_provider.user
            await self.auth_commands.update_last_used(auth_provider)
        else:
            # Provider belum ada, cek apakah user sudah terdaftar via email
            if not google_user.email:
                raise UnauthorizedException("User tidak terdaftar dalam sistem")

            user = await self.user_queries.get_by_email(google_user.email)
            if not user:
                raise UnauthorizedException("User tidak terdaftar dalam sistem")

            # Auto-link Google provider ke user yang sudah ada
            await self.auth_commands.create(
                user_id=user.id,
                provider=AuthProvider.GOOGLE.value,
                provider_user_id=google_user.google_id,
            )
            logger.info(f"Auto-linked Google provider ke user: {user.id}")

        # Auto-save avatar jika belum ada
        if google_user.picture and not user.avatar_path:
            try:
                avatar_path = await download_and_upload_avatar_from_url(
                    avatar_url=google_user.picture,
                    user_id=user.id,
                    old_avatar_path=user.avatar_path,
                )
                if avatar_path:
                    user.avatar_path = avatar_path
                    await self.user_commands.session.flush()
            except Exception as e:
                logger.warning(f"Failed to auto-save avatar: {e}")

        # Validasi client access
        app = await self.client_validator.validate_client_access(
            user_id=str(user.id), client_id=client_id
        )

        single_session = app.single_session if app else False

        logger.info(f"Google login: {user.id} -> {client_id or 'SSO'}")

        # Generate tokens dan create sessions
        return await self.token_helper.create_login_response(
            user=user,
            client_id=client_id,
            single_session=single_session,
            device_id=device_id,
            device_info=device_info,
            ip_address=ip_address,
            fcm_token=fcm_token,
        )
