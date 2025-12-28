"""
Create User Use Case
"""

import logging
from typing import Optional

from fastapi import UploadFile

from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.users.schemas import UserCreateRequest
from app.modules.users.models.user import User
from app.modules.users.utils.events import UserEventUtil
from app.core.utils.file_upload import upload_file_to_gcp
from app.core.messaging import EventPublisher

logger = logging.getLogger(__name__)


class CreateUserUseCase:
    """Use Case for creating a new user."""

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
        data: UserCreateRequest,
        avatar_file: Optional[UploadFile] = None,
    ) -> User:
        """Execute the create user use case. Returns raw User model."""
        user = await self.commands.create(
            name=data.name,
            email=data.email,
            phone=data.phone,
            avatar_path=data.avatar_path,
            gender=data.gender,
            role=data.role,
            status=data.status,
        )
        logger.info(f"User created: {user.id}")

        if avatar_file and avatar_file.filename:
            try:
                _, avatar_path = await upload_file_to_gcp(
                    file=avatar_file,
                    entity_type="users",
                    entity_id=str(user.id),
                    subfolder="avatar"
                )
                user.avatar_path = avatar_path
                logger.info(f"Avatar uploaded for user {user.id}: {avatar_path}")
            except Exception as e:
                logger.error(f"Failed to upload avatar for user {user.id}: {e}")

        return user
