"""
User Module Dependencies
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.modules.users.repositories import UserQueries, UserCommands
from app.core.messaging import EventPublisher, event_publisher

from app.modules.users.services.user_service import UserService


def get_user_queries(db: AsyncSession = Depends(get_db)) -> UserQueries:
    return UserQueries(db)


UserQueriesDep = Annotated[UserQueries, Depends(get_user_queries)]


def get_user_commands(db: AsyncSession = Depends(get_db)) -> UserCommands:
    return UserCommands(db)


UserCommandsDep = Annotated[UserCommands, Depends(get_user_commands)]


def get_event_publisher() -> EventPublisher:
    return event_publisher


EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher)]


def get_user_service(
    queries: UserQueriesDep,
    commands: UserCommandsDep,
    publisher: EventPublisherDep,
) -> UserService:
    return UserService(
        queries,
        commands,
        publisher,
    )


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
