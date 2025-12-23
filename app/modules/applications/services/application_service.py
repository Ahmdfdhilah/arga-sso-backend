"""
Application Service - Facade for Application operations
Delegates business logic to specific Use Cases.
Handles schema conversion (Model -> Response).
"""

from typing import Optional, List, Tuple
import logging

from fastapi import UploadFile

# Repositories
from app.modules.applications.repositories import ApplicationQueries, ApplicationCommands

# Schemas
from app.modules.applications.schemas import (
    ApplicationResponse,
    ApplicationListItemResponse,
    AllowedAppResponse,
)

# Use Cases
from app.modules.applications.use_cases.create_application import CreateApplicationUseCase
from app.modules.applications.use_cases.update_application import UpdateApplicationUseCase
from app.modules.applications.use_cases.delete_application import DeleteApplicationUseCase
from app.modules.applications.use_cases.get_application import GetApplicationUseCase
from app.modules.applications.use_cases.list_applications import ListApplicationsUseCase
from app.modules.applications.use_cases.get_user_applications import GetUserApplicationsUseCase
from app.modules.applications.use_cases.assign_applications_to_user import AssignApplicationsToUserUseCase
from app.modules.applications.use_cases.remove_application_from_user import RemoveApplicationFromUserUseCase

logger = logging.getLogger(__name__)


class ApplicationService:
    """
    Facade Service for Application operations.
    Delegates business logic to specific Use Cases.
    Handles Response Building (Model -> Schema).
    """

    def __init__(
        self,
        queries: ApplicationQueries,
        commands: ApplicationCommands,
    ):
        self.queries = queries
        self.commands = commands

        # Initialize Use Cases - Application CRUD
        self.create_uc = CreateApplicationUseCase(queries, commands)
        self.update_uc = UpdateApplicationUseCase(queries, commands)
        self.delete_uc = DeleteApplicationUseCase(queries, commands)
        self.get_uc = GetApplicationUseCase(queries)
        self.list_uc = ListApplicationsUseCase(queries)
        
        # Initialize Use Cases - User-Application Assignment
        self.get_user_apps_uc = GetUserApplicationsUseCase(queries)
        self.assign_apps_uc = AssignApplicationsToUserUseCase(queries, commands)
        self.remove_app_uc = RemoveApplicationFromUserUseCase(commands)

    # --- Application CRUD Operations ---

    async def create(
        self,
        name: str,
        code: str,
        base_url: str,
        description: Optional[str] = None,
        single_session: bool = False,
        img_file: Optional[UploadFile] = None,
        icon_file: Optional[UploadFile] = None,
    ) -> ApplicationResponse:
        """Create a new application."""
        app = await self.create_uc.execute(
            name=name,
            code=code,
            base_url=base_url,
            description=description,
            single_session=single_session,
            img_file=img_file,
            icon_file=icon_file,
        )
        return ApplicationResponse.model_validate(app)

    async def update(
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
        """Update an existing application."""
        app = await self.update_uc.execute(
            app_id=app_id,
            name=name,
            code=code,
            base_url=base_url,
            description=description,
            is_active=is_active,
            single_session=single_session,
            img_file=img_file,
            icon_file=icon_file,
        )
        return ApplicationResponse.model_validate(app)

    async def delete(self, app_id: str) -> None:
        """Delete an application."""
        await self.delete_uc.execute(app_id)

    async def get(self, app_id: str) -> ApplicationResponse:
        """Get application by ID."""
        app = await self.get_uc.execute(app_id)
        return ApplicationResponse.model_validate(app)

    async def get_by_code(self, code: str) -> Optional[ApplicationResponse]:
        """Get application by code."""
        app = await self.get_uc.execute_by_code(code)
        return ApplicationResponse.model_validate(app) if app else None

    async def list(
        self,
        page: int = 1,
        limit: int = 20,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[ApplicationListItemResponse], int]:
        """List applications with pagination."""
        apps, total = await self.list_uc.execute(page, limit, is_active)
        items = [ApplicationListItemResponse.model_validate(a) for a in apps]
        return items, total

    # --- User-Application Assignment Operations ---

    async def get_user_applications(self, user_id: str) -> List[AllowedAppResponse]:
        """Get applications assigned to a user."""
        apps = await self.get_user_apps_uc.execute(user_id)
        return [AllowedAppResponse.model_validate(a) for a in apps]

    async def assign_applications_to_user(
        self, user_id: str, application_ids: List[str]
    ) -> List[AllowedAppResponse]:
        """Sync user's applications. Adds new ones, removes ones not in list."""
        apps = await self.assign_apps_uc.execute(user_id, application_ids)
        return [AllowedAppResponse.model_validate(a) for a in apps]

    async def remove_application_from_user(
        self, user_id: str, application_id: str
    ) -> None:
        """Remove a single application from user."""
        await self.remove_app_uc.execute(user_id, application_id)
