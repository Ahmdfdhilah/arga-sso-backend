"""
Delete User Use Case
"""

import logging
from typing import Optional

from app.core.exceptions import NotFoundException
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.users.utils.events import UserEventUtil
from app.core.messaging import EventPublisher

logger = logging.getLogger(__name__)


class DeleteUserUseCase:
    """Use Case for deleting a user."""

    def __init__(
        self,
        queries: UserQueries,
        commands: UserCommands,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.queries = queries
        self.commands = commands
        self.event_publisher = event_publisher

    async def execute(self, user_id: str) -> None:
        """Execute the delete user use case."""
        user = await self.queries.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} tidak ditemukan")

        # Publish event before delete (need user data)
        await UserEventUtil.publish(self.event_publisher, "deleted", user)

        # Delete user
        await self.commands.delete(user)
        logger.info(f"User deleted: {user_id}")
