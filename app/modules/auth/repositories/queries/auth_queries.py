from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models.auth_provider import AuthProvider
from app.modules.users.models.user import User


class AuthProviderQueries:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, provider_id: int) -> Optional[AuthProvider]:
        stmt = select(AuthProvider).where(AuthProvider.id == provider_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_provider_user_id(
        self, provider: str, provider_user_id: str
    ) -> Optional[AuthProvider]:
        stmt = (
            select(AuthProvider)
            .join(User)
            .where(
                AuthProvider.provider == provider,
                AuthProvider.provider_user_id == provider_user_id,
                User.deleted_at.is_(None),
            )
            .options(selectinload(AuthProvider.user))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> list[AuthProvider]:
        stmt = select(AuthProvider).where(AuthProvider.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
