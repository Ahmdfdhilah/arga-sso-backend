import logging
from typing import Optional, List, Tuple

from app.core.exceptions import NotFoundException, ConflictException
from app.modules.applications.repositories import (
    ApplicationQueries,
    ApplicationCommands,
)
from app.modules.applications.schemas import (
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
    ApplicationResponse,
    ApplicationListItemResponse,
)

logger = logging.getLogger(__name__)


class ApplicationCrudService:
    """Service for Application CRUD operations."""

    def __init__(
        self,
        app_queries: ApplicationQueries,
        app_commands: ApplicationCommands,
    ):
        self.app_queries = app_queries
        self.app_commands = app_commands

    async def get_application(self, app_id: str) -> ApplicationResponse:
        app = await self.app_queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")
        return ApplicationResponse.model_validate(app)

    async def get_application_by_code(self, code: str) -> ApplicationResponse:
        app = await self.app_queries.get_by_code(code)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")
        return ApplicationResponse.model_validate(app)

    async def list_applications(
        self,
        page: int = 1,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[ApplicationListItemResponse], int]:
        """Return list of applications with total count for pagination."""
        offset = (page - 1) * limit
        apps, total = await self.app_queries.list_applications(
            limit=limit, offset=offset, is_active=is_active
        )
        return [ApplicationListItemResponse.model_validate(a) for a in apps], total

    async def create_application(
        self, data: ApplicationCreateRequest
    ) -> ApplicationResponse:
        existing = await self.app_queries.get_by_code(data.code)
        if existing:
            raise ConflictException(f"Aplikasi dengan kode '{data.code}' sudah ada")

        app = await self.app_commands.create(
            name=data.name,
            code=data.code,
            base_url=data.base_url,
            description=data.description,
        )
        logger.info(f"Application created: {app.id} ({app.code})")
        return ApplicationResponse.model_validate(app)

    async def update_application(
        self, app_id: str, data: ApplicationUpdateRequest
    ) -> ApplicationResponse:
        app = await self.app_queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")

        if data.code and data.code != app.code:
            existing = await self.app_queries.get_by_code(data.code)
            if existing:
                raise ConflictException(f"Aplikasi dengan kode '{data.code}' sudah ada")

        updated = await self.app_commands.update(app, data)
        logger.info(f"Application updated: {app_id}")
        return ApplicationResponse.model_validate(updated)

    async def delete_application(self, app_id: str) -> None:
        app = await self.app_queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")
        await self.app_commands.delete(app)
        logger.info(f"Application deleted: {app_id}")
