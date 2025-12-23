"""
Application Module Dependencies
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.modules.applications.repositories import ApplicationQueries, ApplicationCommands

from app.modules.applications.services.application_service import ApplicationService


def get_app_queries(db: AsyncSession = Depends(get_db)) -> ApplicationQueries:
    return ApplicationQueries(db)


ApplicationQueriesDep = Annotated[ApplicationQueries, Depends(get_app_queries)]


def get_app_commands(db: AsyncSession = Depends(get_db)) -> ApplicationCommands:
    return ApplicationCommands(db)


ApplicationCommandsDep = Annotated[ApplicationCommands, Depends(get_app_commands)]


def get_application_service(
    queries: ApplicationQueriesDep,
    commands: ApplicationCommandsDep,
) -> ApplicationService:
    return ApplicationService(queries, commands)


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
