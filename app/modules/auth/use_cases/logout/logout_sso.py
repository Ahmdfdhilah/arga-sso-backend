"""Use case untuk logout SSO session saja."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService
    from app.modules.auth.services.sso_session_service import SSOSessionService

logger = logging.getLogger(__name__)


class LogoutSSOUseCase:
    """
    Use case untuk logout SSO session saja.
    Menginvalidasi SSO token tapi tetap menjaga app sessions aktif.
    Digunakan oleh SSO frontend yang bukan registered client.
    """

    def __init__(
        self,
        session_service: "SessionService",
        sso_session_service: "SSOSessionService",
    ):
        self.session_service = session_service
        self.sso_session_service = sso_session_service

    async def execute(self, user_id: str) -> None:
        """
        Logout SSO session saja tanpa menghapus app sessions.

        Args:
            user_id: User ID yang akan di-logout dari SSO
        """
        logger.info(f"SSO logout attempt untuk user {user_id}")

        # Hapus SSO session
        await self.sso_session_service.delete_sso_session(user_id)

        # Hapus session untuk sso_portal client
        await self.session_service.delete_client_sessions(user_id, "sso_portal")

        logger.info(f"User {user_id} SSO session deleted")
