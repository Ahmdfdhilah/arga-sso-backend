"""
User Service - Facade for User operations
Delegates business logic to specific Use Cases.
Handles schema conversion (Model -> Response).
"""

from typing import Optional, List, Tuple
import logging

from fastapi import UploadFile

# Repositories
from app.modules.users.repositories import UserQueries, UserCommands
from app.core.messaging import EventPublisher

# Schemas
from app.modules.users.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListItemResponse,
)

# Use Cases
from app.modules.users.use_cases.create_user import CreateUserUseCase
from app.modules.users.use_cases.update_user import UpdateUserUseCase
from app.modules.users.use_cases.delete_user import DeleteUserUseCase
from app.modules.users.use_cases.get_user import GetUserUseCase
from app.modules.users.use_cases.list_users import ListUsersUseCase

# Utils
from app.modules.auth.utils.token_helper import TokenHelper
from app.core.enums import UserRole, UserStatus

logger = logging.getLogger(__name__)


class UserService:
    """
    Facade Service for User operations.
    Delegates business logic to specific Use Cases.
    Handles Response Building (Model -> Schema).
    """

    def __init__(
        self,
        queries: UserQueries,
        commands: UserCommands,
        event_publisher: Optional[EventPublisher] = None,
    ):
        self.queries = queries
        self.commands = commands
        self.event_publisher = event_publisher

        # Initialize Use Cases
        self.create_uc = CreateUserUseCase(queries, commands, event_publisher)
        self.update_uc = UpdateUserUseCase(queries, commands, event_publisher)
        self.delete_uc = DeleteUserUseCase(queries, commands, event_publisher)
        self.get_uc = GetUserUseCase(queries)
        self.list_uc = ListUsersUseCase(queries)

    def _build_response(self, user) -> UserResponse:
        """Build UserResponse with joined data."""
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

    # --- Write Operations ---

    async def create(
        self,
        data: UserCreateRequest,
        avatar_file: Optional[UploadFile] = None,
    ) -> UserResponse:
        """Create a new user."""
        user = await self.create_uc.execute(data, avatar_file)
        return self._build_response(user)

    async def update(
        self,
        user_id: str,
        data: UserUpdateRequest,
        avatar_file: Optional[UploadFile] = None,
    ) -> UserResponse:
        """Update an existing user."""
        user = await self.update_uc.execute(user_id, data, avatar_file)
        return self._build_response(user)

    async def delete(self, user_id: str) -> None:
        """Delete a user."""
        await self.delete_uc.execute(user_id)

    # --- Read Operations ---

    async def get(self, user_id: str) -> UserResponse:
        """Get user by ID."""
        user = await self.get_uc.execute(user_id)
        return self._build_response(user)

    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        """Get user by email."""
        user = await self.get_uc.execute_by_email(email)
        return self._build_response(user) if user else None

    async def list(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[UserListItemResponse], int]:
        """List users with pagination."""
        users, total = await self.list_uc.execute(page, limit, status, role, search)
        items = [UserListItemResponse.model_validate(u) for u in users]
        return items, total
