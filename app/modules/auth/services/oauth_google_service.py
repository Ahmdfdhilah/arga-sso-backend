"""OAuth2 Google service facade."""

import logging
from typing import Optional, Dict, Any

from app.modules.auth.repositories import AuthProviderQueries, AuthProviderCommands
from app.modules.auth.services.session_service import SessionService
from app.modules.auth.services.sso_session_service import SSOSessionService
from app.modules.auth.schemas import LoginResponse
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)
from app.modules.auth.use_cases.google.get_authorization_url import (
    GoogleOAuthGetAuthorizationURLUseCase,
)
from app.modules.auth.use_cases.google.handle_callback import (
    GoogleOAuthHandleCallbackUseCase,
)

logger = logging.getLogger(__name__)


class OAuth2GoogleService:
    """
    OAuth2 Google service facade.
    Mengkoordinasikan use cases untuk Google OAuth2 authentication.
    """

    def __init__(
        self,
        auth_queries: AuthProviderQueries,
        auth_commands: AuthProviderCommands,
        user_queries: UserQueries,
        user_commands: UserCommands,
        session_service: SessionService,
        sso_session_service: SSOSessionService,
        app_queries: ApplicationQueries,
    ):
        # Initialize use cases
        self.get_url_uc = GoogleOAuthGetAuthorizationURLUseCase()
        self.handle_callback_uc = GoogleOAuthHandleCallbackUseCase(
            auth_queries,
            auth_commands,
            user_queries,
            user_commands,
            session_service,
            sso_session_service,
            app_queries,
        )

    def get_authorization_url(
        self, redirect_uri: Optional[str] = None, state: Optional[str] = None
    ) -> str:
        """Generate Google OAuth2 authorization URL."""
        return self.get_url_uc.execute(redirect_uri=redirect_uri, state=state)

    async def handle_callback(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
        client_id: Optional[str] = None,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """Handle OAuth2 Google callback."""
        return await self.handle_callback_uc.execute(
            code=code,
            redirect_uri=redirect_uri,
            client_id=client_id,
            device_id=device_id,
            device_info=device_info,
            ip_address=ip_address,
            fcm_token=fcm_token,
        )
