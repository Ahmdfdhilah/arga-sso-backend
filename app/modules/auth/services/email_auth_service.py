"""Email authentication service facade."""

import logging
from typing import Optional, Dict, Any

from app.modules.auth.repositories import AuthProviderQueries, AuthProviderCommands
from app.modules.auth.services.session_service import SessionService
from app.modules.auth.services.sso_session_service import SSOSessionService
from app.modules.auth.schemas import LoginResponse
from app.modules.users.repositories import UserQueries
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)
from app.modules.auth.use_cases.email.email_login import EmailLoginUseCase

logger = logging.getLogger(__name__)


class EmailAuthService:
    """
    Email authentication service facade.
    Mengkoordinasikan use cases untuk email/password authentication.
    """

    def __init__(
        self,
        auth_queries: AuthProviderQueries,
        auth_commands: AuthProviderCommands,
        user_queries: UserQueries,
        session_service: SessionService,
        sso_session_service: SSOSessionService,
        app_queries: ApplicationQueries,
    ):
        # Initialize use case
        self.email_login_uc = EmailLoginUseCase(
            auth_queries,
            auth_commands,
            user_queries,
            session_service,
            sso_session_service,
            app_queries,
        )

    async def login(
        self,
        email: str,
        password: str,
        client_id: Optional[str] = None,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """Login dengan email dan password."""
        return await self.email_login_uc.execute(
            email=email,
            password=password,
            client_id=client_id,
            device_id=device_id,
            device_info=device_info,
            ip_address=ip_address,
            fcm_token=fcm_token,
        )
