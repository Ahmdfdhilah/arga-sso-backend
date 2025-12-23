"""
Assign Applications to User Use Case
"""

import logging
from typing import List

from app.modules.applications.repositories import ApplicationQueries, ApplicationCommands
from app.modules.applications.models.application import Application
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class AssignApplicationsToUserUseCase:
    """Use Case for assigning applications to a user (sync mode)."""

    def __init__(
        self,
        queries: ApplicationQueries,
        commands: ApplicationCommands,
    ):
        self.queries = queries
        self.commands = commands

    async def execute(
        self, user_id: str, application_ids: List[str]
    ) -> List[Application]:
        """
        Sync user's applications. Adds new ones, removes ones not in list.
        Returns updated list of applications.
        """
        unique_app_ids = set(application_ids)

        # Validate all application IDs exist
        for app_id in unique_app_ids:
            app = await self.queries.get_by_id(app_id)
            if not app:
                raise NotFoundException(f"Aplikasi dengan ID {app_id} tidak ditemukan")

        existing_apps = await self.queries.get_user_applications(user_id)
        existing_app_ids = {str(app.id) for app in existing_apps}

        to_add = unique_app_ids - existing_app_ids
        to_remove = existing_app_ids - unique_app_ids

        if to_add:
            await self.commands.assign_applications_to_user(user_id, list(to_add))
            logger.info(f"Added {len(to_add)} applications to user {user_id}")

        for app_id in to_remove:
            await self.commands.remove_application_from_user(user_id, app_id)
        if to_remove:
            logger.info(f"Removed {len(to_remove)} applications from user {user_id}")

        # Return updated list
        return await self.queries.get_user_applications(user_id)
