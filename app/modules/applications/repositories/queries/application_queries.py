from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.applications.models.application import Application
from app.modules.applications.models.user_application import UserApplication


class ApplicationQueries:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, app_id: str) -> Optional[Application]:
        stmt = select(Application).where(Application.id == app_id, Application.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Application]:
        stmt = select(Application).where(Application.code == code, Application.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_applications(self, user_id: str) -> List[Application]:
        stmt = (
            select(Application)
            .join(UserApplication)
            .where(UserApplication.user_id == user_id, Application.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_applications(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> tuple[List[Application], int]:
        stmt = select(Application).where(Application.deleted_at.is_(None))
        count_stmt = select(func.count(Application.id)).where(Application.deleted_at.is_(None))

        if is_active is not None:
            stmt = stmt.where(Application.is_active == is_active)
            count_stmt = count_stmt.where(Application.is_active == is_active)

        total = await self.session.scalar(count_stmt)
        stmt = stmt.limit(limit).offset(offset).order_by(Application.created_at.desc())
        result = await self.session.execute(stmt)

        return list(result.scalars().all()), total or 0
