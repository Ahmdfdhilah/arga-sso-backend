import logging
from typing import List

from app.core.exceptions import NotFoundException, ConflictException
from app.modules.applications.repositories import (
    ApplicationQueries,
    ApplicationCommands,
)
from app.modules.applications.schemas import AllowedAppResponse

logger = logging.getLogger(__name__)


class UserApplicationService:
    """Service for managing user-application assignments."""

    def __init__(
        self,
        app_queries: ApplicationQueries,
        app_commands: ApplicationCommands,
    ):
        self.app_queries = app_queries
        self.app_commands = app_commands

    async def get_user_applications(self, user_id: str) -> List[AllowedAppResponse]:
        apps = await self.app_queries.get_user_applications(user_id)
        # Return full application objects so AllowedAppResponse can map all fields
        return [AllowedAppResponse.model_validate(a) for a in apps]


    async def assign_applications_to_user(
        self, user_id: str, application_ids: List[str]
    ) -> List[AllowedAppResponse]:
        """Sync user's applications. Adds new ones, removes ones not in list."""
        unique_app_ids = set(application_ids)

        for app_id in unique_app_ids:
            app = await self.app_queries.get_by_id(app_id)
            if not app:
                raise NotFoundException(f"Aplikasi dengan ID {app_id} tidak ditemukan")

        existing_apps = await self.app_queries.get_user_applications(user_id)
        existing_app_ids = {str(app.id) for app in existing_apps}

        to_add = unique_app_ids - existing_app_ids
        to_remove = existing_app_ids - unique_app_ids

        if to_add:
            await self.app_commands.assign_applications_to_user(user_id, list(to_add))
            logger.info(f"Added {len(to_add)} applications to user {user_id}")

        for app_id in to_remove:
            await self.app_commands.remove_application_from_user(user_id, app_id)
        if to_remove:
            logger.info(f"Removed {len(to_remove)} applications from user {user_id}")

        return await self.get_user_applications(user_id)

    async def remove_application_from_user(
        self, user_id: str, application_id: str
    ) -> None:
        await self.app_commands.remove_application_from_user(user_id, application_id)
        logger.info(f"Removed application {application_id} from user {user_id}")
