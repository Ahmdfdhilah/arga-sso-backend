from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.modules.applications.repositories import (
    ApplicationQueries,
    ApplicationCommands,
)
from app.modules.applications.services import (
    ApplicationCrudService,
    UserApplicationService,
)


def get_app_queries(db: AsyncSession = Depends(get_db)) -> ApplicationQueries:
    return ApplicationQueries(db)


def get_app_commands(db: AsyncSession = Depends(get_db)) -> ApplicationCommands:
    return ApplicationCommands(db)


def get_application_crud_service(
    app_queries: ApplicationQueries = Depends(get_app_queries),
    app_commands: ApplicationCommands = Depends(get_app_commands),
) -> ApplicationCrudService:
    return ApplicationCrudService(app_queries=app_queries, app_commands=app_commands)


def get_user_application_service(
    app_queries: ApplicationQueries = Depends(get_app_queries),
    app_commands: ApplicationCommands = Depends(get_app_commands),
) -> UserApplicationService:
    return UserApplicationService(app_queries=app_queries, app_commands=app_commands)


ApplicationQueriesDep = Annotated[ApplicationQueries, Depends(get_app_queries)]
ApplicationCommandsDep = Annotated[ApplicationCommands, Depends(get_app_commands)]
ApplicationCrudServiceDep = Annotated[
    ApplicationCrudService, Depends(get_application_crud_service)
]
UserApplicationServiceDep = Annotated[
    UserApplicationService, Depends(get_user_application_service)
]
