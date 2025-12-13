from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models.user import User


class UserQueries:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[User]:
        stmt = select(User).where(User.phone == phone, User.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[User], int]:
        stmt = select(User).where(User.deleted_at.is_(None))

        if status:
            stmt = stmt.where(User.status == status)
        if role:
            stmt = stmt.where(User.role == role)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (User.name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
            )

        count_stmt = select(func.count(User.id)).where(User.deleted_at.is_(None))
        if status:
            count_stmt = count_stmt.where(User.status == status)
        if role:
            count_stmt = count_stmt.where(User.role == role)
        if search:
            search_pattern = f"%{search}%"
            count_stmt = count_stmt.where(
                (User.name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
            )

        total = await self.session.scalar(count_stmt)

        stmt = stmt.limit(limit).offset(offset).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)
        users = list(result.scalars().all())

        return users, total or 0
