from typing import TYPE_CHECKING, Optional

from app.core.exceptions import ForbiddenException, NotFoundException

if TYPE_CHECKING:
    from app.modules.applications.repositories.queries.application_queries import (
        ApplicationQueries,
    )
    from app.modules.applications.models.application import Application


class ClientValidator:
    """
    Utility for validating user access to client applications.

    This is a reusable utility following DRY principle.
    Used across multiple auth services (email, firebase, google oauth).
    """

    def __init__(self, app_queries: "ApplicationQueries"):
        self.app_queries = app_queries

    async def validate_client_access(
        self, user_id: str, client_id: Optional[str]
    ) -> Optional["Application"]:
        """
        Validate that:
        1. Client application exists and is active
        2. User has access to this client

        Args:
            user_id: User UUID string
            client_id: Application client code (None for SSO-only login)

        Returns:
            Application: The validated application model
            None: If client_id is None (SSO-only login, skip validation)

        Raises:
            NotFoundException: If application not found or inactive
            ForbiddenException: If user doesn't have access to application
        """
        # SSO-only login: skip validation
        if client_id is None:
            return None

        # Check if application exists and is active (by code)
        app = await self.app_queries.get_by_code(client_id)
        if not app or not app.is_active:
            raise NotFoundException(
                f"Aplikasi '{client_id}' tidak ditemukan atau tidak aktif"
            )

        # Check if user has access to this application
        user_apps = await self.app_queries.get_user_applications(user_id)
        user_app_ids = [str(a.id) for a in user_apps]

        if str(app.id) not in user_app_ids:
            raise ForbiddenException(
                f"User tidak memiliki akses ke aplikasi '{client_id}'"
            )

        return app
