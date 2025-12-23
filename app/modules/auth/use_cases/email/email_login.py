"""Use case untuk email/password authentication login."""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

from app.core.security import PasswordService
from app.core.exceptions import UnauthorizedException
from app.core.enums import AuthProvider
from app.modules.auth.repositories import AuthProviderQueries, AuthProviderCommands
from app.modules.auth.utils.token_helper import TokenHelper
from app.modules.auth.utils.client_validator import ClientValidator
from app.modules.auth.schemas import LoginResponse
from app.modules.users.repositories import UserQueries
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService
    from app.modules.auth.services.sso_session_service import SSOSessionService

logger = logging.getLogger(__name__)


class EmailLoginUseCase:
    """Use case untuk login menggunakan email dan password."""

    def __init__(
        self,
        auth_queries: AuthProviderQueries,
        auth_commands: AuthProviderCommands,
        user_queries: UserQueries,
        session_service: "SessionService",
        sso_session_service: "SSOSessionService",
        app_queries: ApplicationQueries,
    ):
        self.auth_queries = auth_queries
        self.auth_commands = auth_commands
        self.user_queries = user_queries
        self.session_service = session_service
        self.sso_session_service = sso_session_service
        self.app_queries = app_queries
        self.token_helper = TokenHelper(session_service, sso_session_service)
        self.client_validator = ClientValidator(app_queries)

    async def execute(
        self,
        email: str,
        password: str,
        client_id: Optional[str] = None,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """
        Login dengan email dan password.

        Args:
            email: Email user
            password: Password user
            client_id: Optional application client code
            device_id: Optional device identifier
            device_info: Optional device metadata
            ip_address: Optional IP address
            fcm_token: Optional FCM token untuk push notification

        Returns:
            LoginResponse dengan tokens dan user data

        Raises:
            UnauthorizedException: Email atau password salah
        """
        logger.info(f"Email login attempt untuk: {email} ke client: {client_id or 'SSO'}")

        # Validasi user exists
        user = await self.user_queries.get_by_email(email)
        if not user:
            raise UnauthorizedException("Email atau password salah")

        # Cek auth provider
        auth_provider = await self.auth_queries.get_by_provider_user_id(
            provider=AuthProvider.EMAIL.value,
            provider_user_id=email,
        )
        if not auth_provider or not auth_provider.password_hash:
            raise UnauthorizedException("Email atau password salah")

        # Verify password
        if not PasswordService.verify_password(password, auth_provider.password_hash):
            raise UnauthorizedException("Email atau password salah")

        # Update last used timestamp
        await self.auth_commands.update_last_used(auth_provider)

        # Validasi client access dan get single_session config
        app = await self.client_validator.validate_client_access(
            user_id=str(user.id), client_id=client_id
        )
        single_session = app.single_session if app else False

        logger.info(f"Email login successful: {user.id} -> {client_id or 'SSO'}")

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
