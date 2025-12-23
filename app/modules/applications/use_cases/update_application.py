"""
Update Application Use Case
"""

import logging
import asyncio
from typing import Optional

from fastapi import UploadFile

from app.modules.applications.repositories import ApplicationQueries, ApplicationCommands
from app.modules.applications.models.application import Application
from app.core.utils.file_upload import upload_file_to_gcp
from app.core.utils.gcp_storage import get_gcp_storage_client
from app.core.exceptions import NotFoundException, ConflictException

logger = logging.getLogger(__name__)


class UpdateApplicationUseCase:
    """Use Case for updating an application."""

    def __init__(
        self,
        queries: ApplicationQueries,
        commands: ApplicationCommands,
    ):
        self.queries = queries
        self.commands = commands

    async def execute(
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
    ) -> Application:
        """Execute the update application use case. Returns raw Application model."""
        app = await self.queries.get_by_id(app_id)
        if not app:
            raise NotFoundException("Aplikasi tidak ditemukan")

        # Check code uniqueness if changing
        if code and code != app.code:
            existing = await self.queries.get_by_code(code)
            if existing:
                raise ConflictException(f"Aplikasi dengan kode '{code}' sudah ada")

        # Handle img file upload
        if img_file and img_file.filename:
            try:
                # Delete old image if exists
                if app.img_path:
                    storage_client = get_gcp_storage_client()
                    await asyncio.to_thread(storage_client.delete_file, app.img_path)
                    logger.info(f"Old application image deleted: {app.img_path}")
                
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
                    await asyncio.to_thread(storage_client.delete_file, app.icon_path)
                    logger.info(f"Old application icon deleted: {app.icon_path}")
                
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
        return app
