"""Firebase authentication service facade."""

import logging
from typing import Optional

from app.modules.auth.repositories import AuthProviderQueries, AuthProviderCommands
from app.modules.auth.services.session_service import SessionService
from app.modules.auth.services.sso_session_service import SSOSessionService
from app.modules.auth.schemas import FirebaseLoginRequest, LoginResponse
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)
# Import langsung dari file untuk menghindari circular import
from app.modules.auth.use_cases.firebase.firebase_login import FirebaseLoginUseCase

logger = logging.getLogger(__name__)


class FirebaseAuthService:
    """
    Firebase authentication service facade.
    Mengkoordinasikan use cases untuk Firebase authentication.
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
        # Initialize use case
        self.firebase_login_uc = FirebaseLoginUseCase(
            auth_queries,
            auth_commands,
            user_queries,
            user_commands,
            session_service,
            sso_session_service,
            app_queries,
        )

    async def login(
        self,
        request: FirebaseLoginRequest,
        ip_address: Optional[str] = None,
    ) -> LoginResponse:
        """Login dengan Firebase token."""
        return await self.firebase_login_uc.execute(
            request=request,
            ip_address=ip_address,
        )
