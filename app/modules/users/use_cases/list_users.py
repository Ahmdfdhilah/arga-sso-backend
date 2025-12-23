"""
List Users Use Case
"""

from typing import List, Tuple, Optional

from app.modules.users.repositories import UserQueries
from app.modules.users.models.user import User


class ListUsersUseCase:
    """Use Case for listing users with pagination."""

    def __init__(self, queries: UserQueries):
        self.queries = queries

    async def execute(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[User], int]:
        """Return list of users with total count for pagination. Returns raw User models."""
        offset = (page - 1) * limit
        users, total = await self.queries.list_users(
            limit=limit,
            offset=offset,
            status=status,
            role=role,
            search=search,
        )
        return users, total
