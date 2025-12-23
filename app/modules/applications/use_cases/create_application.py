"""
Create Application Use Case
"""

import logging
from typing import Optional

from fastapi import UploadFile

from app.modules.applications.repositories import ApplicationQueries, ApplicationCommands
from app.modules.applications.models.application import Application
from app.core.utils.file_upload import upload_file_to_gcp
from app.core.exceptions import ConflictException

logger = logging.getLogger(__name__)


class CreateApplicationUseCase:
    """Use Case for creating a new application."""

    def __init__(
        self,
        queries: ApplicationQueries,
        commands: ApplicationCommands,
    ):
        self.queries = queries
        self.commands = commands

    async def execute(
        self,
        name: str,
        code: str,
        base_url: str,
        description: Optional[str] = None,
        single_session: bool = False,
        img_file: Optional[UploadFile] = None,
        icon_file: Optional[UploadFile] = None,
    ) -> Application:
        """Execute the create application use case. Returns raw Application model."""
        # Check for existing code
        existing = await self.queries.get_by_code(code)
        if existing:
            raise ConflictException(f"Aplikasi dengan kode '{code}' sudah ada")

        # Create application
        app = await self.commands.create(
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
                logger.warning(f"Failed to upload application image: {e}")

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
                logger.warning(f"Failed to upload application icon: {e}")

        return app
