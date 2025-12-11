import logging
from typing import Optional, List, Tuple
from fastapi import UploadFile

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
from app.core.utils.file_upload import upload_file_to_gcp
from app.core.utils.gcp_storage import get_gcp_storage_client

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
        self,
        name: str,
        code: str,
        base_url: str,
        description: Optional[str] = None,
        single_session: bool = False,
        img_file: Optional[UploadFile] = None,
        icon_file: Optional[UploadFile] = None,
    ) -> ApplicationResponse:
        existing = await self.app_queries.get_by_code(code)
        if existing:
            raise ConflictException(f"Aplikasi dengan kode '{code}' sudah ada")

        # Create application first to get ID
        app = await self.app_commands.create(
            name=name,
            code=code,
            base_url=base_url,
            description=description,
            single_session=single_session,
        )
        logger.info(f"Application created: {app.id} ({app.code})")

        # Upload files if provided
        if img_file and img_file.filename:
            try:
                _, img_path = await upload_file_to_gcp(
                    file=img_file,
                    entity_type="applications",
                    entity_id=str(app.id),
                    subfolder="img",
                )
                app.img_path = img_path
                logger.info(f"Application image uploaded: {img_path}")
            except Exception as e:
                logger.warning(f"Failed to upload application image: {e}. Continuing without image.")

        if icon_file and icon_file.filename:
            try:
                _, icon_path = await upload_file_to_gcp(
                    file=icon_file,
                    entity_type="applications",
                    entity_id=str(app.id),
                    subfolder="icon",
                )
                app.icon_path = icon_path
                logger.info(f"Application icon uploaded: {icon_path}")
            except Exception as e:
                logger.warning(f"Failed to upload application icon: {e}. Continuing without icon.")

        return ApplicationResponse.model_validate(app)

    async def update_application(
        self,
        app_id: str,
        name: Optional[str] = None,
        code: Optional[str] = None,
        base_url: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        single_session: Optional[bool] = None,
        img_file: Optional[UploadFile] = None,
        icon_file: Optional[UploadFile] = None,
    ) -> ApplicationResponse:
        app = await self.app_queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")

        if code and code != app.code:
            existing = await self.app_queries.get_by_code(code)
            if existing:
                raise ConflictException(f"Aplikasi dengan kode '{code}' sudah ada")

        # Handle img file upload
        if img_file and img_file.filename:
            try:
                # Delete old image if exists
                if app.img_path:
                    storage_client = get_gcp_storage_client()
                    try:
                        import asyncio
                        await asyncio.to_thread(storage_client.delete_file, app.img_path)
                        logger.info(f"Old application image deleted: {app.img_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old application image: {e}")

                # Upload new image
                _, img_path = await upload_file_to_gcp(
                    file=img_file,
                    entity_type="applications",
                    entity_id=str(app.id),
                    subfolder="img",
                )
                app.img_path = img_path
                logger.info(f"Application image updated: {img_path}")
            except Exception as e:
                logger.warning(f"Failed to upload new application image: {e}")

        # Handle icon file upload
        if icon_file and icon_file.filename:
            try:
                # Delete old icon if exists
                if app.icon_path:
                    storage_client = get_gcp_storage_client()
                    try:
                        import asyncio
                        await asyncio.to_thread(storage_client.delete_file, app.icon_path)
                        logger.info(f"Old application icon deleted: {app.icon_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old application icon: {e}")

                # Upload new icon
                _, icon_path = await upload_file_to_gcp(
                    file=icon_file,
                    entity_type="applications",
                    entity_id=str(app.id),
                    subfolder="icon",
                )
                app.icon_path = icon_path
                logger.info(f"Application icon updated: {icon_path}")
            except Exception as e:
                logger.warning(f"Failed to upload new application icon: {e}")

        # Update other fields
        if name is not None:
            app.name = name
        if code is not None:
            app.code = code
        if base_url is not None:
            app.base_url = base_url
        if description is not None:
            app.description = description
        if is_active is not None:
            app.is_active = is_active
        if single_session is not None:
            app.single_session = single_session

        logger.info(f"Application updated: {app_id}")
        return ApplicationResponse.model_validate(app)

    async def delete_application(self, app_id: str) -> None:
        app = await self.app_queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")
        await self.app_commands.delete(app)
        logger.info(f"Application deleted: {app_id}")
