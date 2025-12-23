"""
Remove Application from User Use Case
"""

import logging

from app.modules.applications.repositories import ApplicationCommands

logger = logging.getLogger(__name__)


class RemoveApplicationFromUserUseCase:
    """Use Case for removing a single application from a user."""

    def __init__(self, commands: ApplicationCommands):
        self.commands = commands

    async def execute(self, user_id: str, application_id: str) -> None:
        """Remove a single application from user."""
        await self.commands.remove_application_from_user(user_id, application_id)
        logger.info(f"Removed application {application_id} from user {user_id}")
