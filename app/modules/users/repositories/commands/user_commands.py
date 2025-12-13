import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models.user import User
from app.modules.users.schemas.requests import UserUpdateRequest
from app.core.enums import UserRole, UserStatus


class UserCommands:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_path: Optional[str] = None,
        role: UserRole = UserRole.USER,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> User:
        user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            phone=phone,
            avatar_path=avatar_path,
            role=role.value if isinstance(role, UserRole) else role,
            status=status.value if isinstance(status, UserStatus) else status,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, data: UserUpdateRequest) -> User:
        """
        Update user with partial data.
        Uses exclude_unset=True to only update fields that were explicitly set.
        This allows:
        - Partial updates (only send fields to update)
        - Setting fields to None (to clear nullable fields)
        """
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if isinstance(value, (UserRole, UserStatus)):
                setattr(user, key, value.value)
            else:
                setattr(user, key, value)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        user.status = UserStatus.DELETED.value
        user.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
