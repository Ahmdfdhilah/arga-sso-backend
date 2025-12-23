"""Use case untuk logout dari specific client (all devices)."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService

logger = logging.getLogger(__name__)


class LogoutClientUseCase:
    """Use case untuk logout dari specific client (semua devices untuk client tersebut)."""

    def __init__(self, session_service: "SessionService"):
        self.session_service = session_service

    async def execute(self, user_id: str, client_id: str) -> None:
        """
        Logout dari specific client (all devices).

        Args:
            user_id: User ID yang akan di-logout
            client_id: Client ID aplikasi yang akan di-logout
        """
        logger.info(f"Client logout attempt untuk user {user_id}, client {client_id}")

        # Hapus semua sessions untuk client ini (all devices)
        await self.session_service.delete_client_sessions(user_id, client_id)

        logger.info(f"User {user_id} logged out dari client {client_id} (all devices)")
