"""
Update User Use Case
"""

import logging
from typing import Optional
import asyncio

from fastapi import UploadFile

from app.core.exceptions import NotFoundException
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.users.schemas import UserUpdateRequest
from app.modules.users.models.user import User
from app.modules.users.utils.events import UserEventUtil
from app.core.utils.file_upload import upload_file_to_gcp
from app.core.utils.gcp_storage import get_gcp_storage_client
from app.core.messaging import EventPublisher

logger = logging.getLogger(__name__)


class UpdateUserUseCase:
    """Use Case for updating a user."""

    def __init__(
        self,
        queries: UserQueries,
        commands: UserCommands,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.queries = queries
        self.commands = commands
        self.event_publisher = event_publisher

    async def execute(
        self,
        user_id: str,
        data: UserUpdateRequest,
        avatar_file: Optional[UploadFile] = None,
    ) -> User:
        """Execute the update user use case. Returns raw User model."""
        user = await self.queries.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} tidak ditemukan")

        # Handle avatar upload
        if avatar_file and avatar_file.filename:
            try:
                _, avatar_path = await upload_file_to_gcp(
                    file=avatar_file,
                    entity_type="users",
                    entity_id=str(user.id),
                    subfolder="avatar"
                )

                # Delete old avatar if exists
                if user.avatar_path:
                    try:
                        storage_client = get_gcp_storage_client()
                        await asyncio.to_thread(storage_client.delete_file, user.avatar_path)
                        logger.info(f"Old avatar deleted: {user.avatar_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old avatar: {e}")

                user.avatar_path = avatar_path
                logger.info(f"Avatar uploaded for user {user_id}: {avatar_path}")
            except Exception as e:
                logger.error(f"Failed to upload avatar for user {user_id}: {e}")

        # Update user fields
        updated_user = await self.commands.update(user, data)
        logger.info(f"User updated: {user_id}")

        # Publish event
        await UserEventUtil.publish(self.event_publisher, "updated", updated_user)

        return updated_user
