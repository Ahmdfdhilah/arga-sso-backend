"""
Get Application Use Case
"""

from typing import Optional

from app.modules.applications.repositories import ApplicationQueries
from app.modules.applications.models.application import Application
from app.core.exceptions import NotFoundException


class GetApplicationUseCase:
    """Use Case for getting a single application."""

    def __init__(self, queries: ApplicationQueries):
        self.queries = queries

    async def execute(self, app_id: str) -> Application:
        """Get application by ID. Returns raw Application model."""
        app = await self.queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")
        return app

    async def execute_by_code(self, code: str) -> Optional[Application]:
        """Get application by code. Returns None if not found."""
        return await self.queries.get_by_code(code)
