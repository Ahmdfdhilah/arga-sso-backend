import logging
from typing import Optional, List, Tuple
from fastapi import UploadFile

from app.core.exceptions import NotFoundException
from app.core.utils.file_upload import upload_file_to_gcp, delete_file_from_gcp_url
from app.core.messaging import event_publisher
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.users.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListItemResponse,
    AllowedApp,
)
from app.modules.users.models.user import User
from app.modules.auth.utils.token_helper import TokenHelper

logger = logging.getLogger(__name__)


class UserCrudService:
    def __init__(self, user_queries: UserQueries, user_commands: UserCommands):
        self.user_queries = user_queries
        self.user_commands = user_commands

    def _build_user_response(self, user: User) -> UserResponse:
        """Build UserResponse with joined data."""
        from app.core.enums import UserRole, UserStatus
        
        allowed_apps, _ = TokenHelper.extract_allowed_apps_from_user(user)

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            phone=user.phone,
            avatar_path=user.avatar_path,
            gender=user.gender,
            status=UserStatus(user.status),
            role=UserRole(user.role),
            created_at=user.created_at,
            updated_at=user.updated_at,
            allowed_apps=allowed_apps,
        )

    def _user_to_event_data(self, user: User) -> dict:
        """Convert user to event payload."""
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "gender": user.gender,
            "avatar_path": user.avatar_path,
            "status": user.status,
            "role": user.role,
        }

    async def get_user_by_id(self, user_id: str) -> UserResponse:
        user = await self.user_queries.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} tidak ditemukan")
        return self._build_user_response(user)

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        user = await self.user_queries.get_by_email(email)
        if not user:
            return None
        return self._build_user_response(user)

    async def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[UserListItemResponse], int]:
        """Return list of users with total count for pagination."""
        offset = (page - 1) * limit
        users, total = await self.user_queries.list_users(
            limit=limit,
            offset=offset,
            status=status,
            role=role,
            search=search,
        )
        return [UserListItemResponse.model_validate(u) for u in users], total

    async def create_user(self, data: UserCreateRequest) -> UserResponse:
        user = await self.user_commands.create(
            name=data.name,
            email=data.email,
            phone=data.phone,
            avatar_path=data.avatar_path,
            gender=data.gender,
            role=data.role,
            status=data.status,
        )
        logger.info(f"User created: {user.id}")
        
        # Publish event for other services
        await event_publisher.publish_user_created(
            str(user.id),
            self._user_to_event_data(user)
        )
        
        return self._build_user_response(user)

    async def update_user(
        self,
        user_id: str,
        data: UserUpdateRequest,
        avatar_file: Optional[UploadFile] = None
    ) -> UserResponse:
        """
        Update user profile with optional avatar upload.
        - If avatar_file provided: upload to GCP and update avatar_path
        - If avatar_file not provided: only update other fields
        """
        user = await self.user_queries.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} tidak ditemukan")

        if avatar_file and avatar_file.filename:
            try:
        
                signed_url, avatar_path = await upload_file_to_gcp(
                    file=avatar_file,
                    entity_type="users",
                    entity_id=str(user.id),
                    subfolder="avatar"
                )

            
                if user.avatar_path:
                    try:
                        from app.core.utils.gcp_storage import get_gcp_storage_client
                        storage_client = get_gcp_storage_client()
                        import asyncio
                        await asyncio.to_thread(storage_client.delete_file, user.avatar_path)
                        logger.info(f"Old avatar deleted: {user.avatar_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old avatar: {e}")

         
                user.avatar_path = avatar_path
                logger.info(f"Avatar uploaded for user {user_id}: {avatar_path}")
            except Exception as e:
                logger.error(f"Failed to upload avatar for user {user_id}: {e}")

        updated_user = await self.user_commands.update(user, data)
        logger.info(f"User updated: {user_id}")
        
        # Publish event for other services
        await event_publisher.publish_user_updated(
            str(updated_user.id),
            self._user_to_event_data(updated_user)
        )
        
        return self._build_user_response(updated_user)

    async def delete_user(self, user_id: str) -> None:
        user = await self.user_queries.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} tidak ditemukan")
        
        # Capture data before delete
        event_data = self._user_to_event_data(user)
        
        await self.user_commands.delete(user)
        logger.info(f"User deleted: {user_id}")
        
        # Publish event for other services
        await event_publisher.publish_user_deleted(user_id, event_data)
