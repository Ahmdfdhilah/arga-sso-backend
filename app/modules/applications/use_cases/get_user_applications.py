"""
Get User Applications Use Case
"""

from typing import List

from app.modules.applications.repositories import ApplicationQueries
from app.modules.applications.models.application import Application


class GetUserApplicationsUseCase:
    """Use Case for getting applications assigned to a user."""

    def __init__(self, queries: ApplicationQueries):
        self.queries = queries

    async def execute(self, user_id: str) -> List[Application]:
        """Get applications assigned to a user. Returns raw Application models."""
        return await self.queries.get_user_applications(user_id)
