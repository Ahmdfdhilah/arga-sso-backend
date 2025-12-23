"""
List Applications Use Case
"""

from typing import List, Tuple, Optional

from app.modules.applications.repositories import ApplicationQueries
from app.modules.applications.models.application import Application


class ListApplicationsUseCase:
    """Use Case for listing applications with pagination."""

    def __init__(self, queries: ApplicationQueries):
        self.queries = queries

    async def execute(
        self,
        page: int = 1,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Application], int]:
        """Return list of applications with total count. Returns raw Application models."""
        offset = (page - 1) * limit
        apps, total = await self.queries.list_applications(
            limit=limit, offset=offset, is_active=is_active
        )
        return apps, total
