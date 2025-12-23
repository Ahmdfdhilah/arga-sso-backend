"""
Get User Use Case
"""

from typing import Optional

from app.core.exceptions import NotFoundException
from app.modules.users.repositories import UserQueries
from app.modules.users.models.user import User


class GetUserUseCase:
    """Use Case for getting a single user."""

    def __init__(self, queries: UserQueries):
        self.queries = queries

    async def execute(self, user_id: str) -> User:
        """Get user by ID. Returns raw User model."""
        user = await self.queries.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} tidak ditemukan")
        return user

    async def execute_by_email(self, email: str) -> Optional[User]:
        """Get user by email, returns None if not found."""
        return await self.queries.get_by_email(email)
