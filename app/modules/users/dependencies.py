from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.users.services import UserCrudService


def get_user_queries(db: AsyncSession = Depends(get_db)) -> UserQueries:
    return UserQueries(db)


def get_user_commands(db: AsyncSession = Depends(get_db)) -> UserCommands:
    return UserCommands(db)


def get_user_crud_service(
    user_queries: UserQueries = Depends(get_user_queries),
    user_commands: UserCommands = Depends(get_user_commands),
) -> UserCrudService:
    return UserCrudService(user_queries=user_queries, user_commands=user_commands)


UserQueriesDep = Annotated[UserQueries, Depends(get_user_queries)]
UserCommandsDep = Annotated[UserCommands, Depends(get_user_commands)]
UserCrudServiceDep = Annotated[UserCrudService, Depends(get_user_crud_service)]
