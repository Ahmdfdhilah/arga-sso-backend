"""
Delete Application Use Case
"""

import logging

from app.modules.applications.repositories import ApplicationQueries, ApplicationCommands
from app.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class DeleteApplicationUseCase:
    """Use Case for deleting an application."""

    def __init__(
        self,
        queries: ApplicationQueries,
        commands: ApplicationCommands,
    ):
        self.queries = queries
        self.commands = commands

    async def execute(self, app_id: str) -> None:
        """Execute the delete application use case."""
        app = await self.queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")

        await self.commands.delete(app)
        logger.info(f"Application deleted: {app_id}")
