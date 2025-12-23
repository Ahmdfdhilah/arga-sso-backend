"""Use case untuk logout dari specific device di specific client."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService

logger = logging.getLogger(__name__)


class LogoutClientDeviceUseCase:
    """Use case untuk logout dari specific device di specific client."""

    def __init__(self, session_service: "SessionService"):
        self.session_service = session_service

    async def execute(self, user_id: str, client_id: str, device_id: str) -> None:
        """
        Logout dari specific device untuk specific client.

        Args:
            user_id: User ID yang akan di-logout
            client_id: Client ID aplikasi
            device_id: Device ID yang akan di-logout
        """
        logger.info(
            f"Client device logout untuk user {user_id}, "
            f"client {client_id}, device {device_id}"
        )

        # Hapus session untuk device ini di client ini
        await self.session_service.delete_client_device_session(
            user_id, client_id, device_id
        )

        logger.info(
            f"User {user_id} logged out dari client {client_id}, device {device_id}"
        )
