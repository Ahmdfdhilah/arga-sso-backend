"""Use case untuk logout dari semua aplikasi dan semua devices."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService
    from app.modules.auth.services.sso_session_service import SSOSessionService

logger = logging.getLogger(__name__)


class LogoutAllUseCase:
    """Use case untuk logout dari semua clients dan semua devices."""

    def __init__(
        self,
        session_service: "SessionService",
        sso_session_service: "SSOSessionService",
    ):
        self.session_service = session_service
        self.sso_session_service = sso_session_service

    async def execute(self, user_id: str) -> None:
        """
        Logout dari semua clients dan semua devices.
        Menghapus SSO session dan semua app sessions.

        Args:
            user_id: User ID yang akan di-logout
        """
        logger.info(f"Logout all attempt untuk user {user_id}")

        # Hapus semua app sessions (all clients, all devices)
        await self.session_service.delete_all_sessions(user_id)

        # Hapus SSO session
        await self.sso_session_service.delete_sso_session(user_id)

        logger.info(f"User {user_id} logged out dari semua clients dan devices")
