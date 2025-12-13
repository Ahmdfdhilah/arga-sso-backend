from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.users.services import UserCrudService


def get_user_crud_service(
    db: AsyncSession = Depends(get_db),
) -> UserCrudService:
    """
    Create UserCrudService with shared database session.
    CRITICAL: UserQueries and UserCommands MUST share the same session
    for proper transaction handling (flush + commit in same session).
    """
    user_queries = UserQueries(db)
    user_commands = UserCommands(db)
    return UserCrudService(user_queries=user_queries, user_commands=user_commands)


UserCrudServiceDep = Annotated[UserCrudService, Depends(get_user_crud_service)]
