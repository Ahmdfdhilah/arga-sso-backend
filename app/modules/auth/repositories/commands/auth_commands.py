import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models.auth_provider import AuthProvider


class AuthProviderCommands:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        provider: str,
        provider_user_id: str,
        password_hash: Optional[str] = None,
    ) -> AuthProvider:
        auth_provider = AuthProvider(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            password_hash=password_hash,
        )
        self.session.add(auth_provider)
        await self.session.flush()
        await self.session.refresh(auth_provider)
        return auth_provider

    async def update_last_used(self, auth_provider: AuthProvider) -> AuthProvider:
        auth_provider.last_used_at = datetime.now(timezone.utc)
        await self.session.flush()
        return auth_provider

    async def delete(self, auth_provider: AuthProvider) -> None:
        await self.session.delete(auth_provider)
        await self.session.flush()
