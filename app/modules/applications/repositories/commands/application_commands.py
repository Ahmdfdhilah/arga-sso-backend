import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.modules.applications.models.application import Application
from app.modules.applications.models.user_application import UserApplication
from app.modules.applications.schemas import ApplicationUpdateRequest


class ApplicationCommands:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        code: str,
        base_url: str,
        description: Optional[str] = None,
        is_active: bool = True,
        single_session: bool = False,
    ) -> Application:
        application = Application(
            id=uuid.uuid4(),
            name=name,
            code=code,
            base_url=base_url,
            description=description,
            is_active=is_active,
            single_session=single_session,
        )
        self.session.add(application)
        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def update(
        self, app: Application, data: ApplicationUpdateRequest
    ) -> Application:
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(app, key, value)
        await self.session.flush()
        await self.session.refresh(app)
        return app

    async def delete(self, app: Application) -> None:
        app.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def assign_applications_to_user(
        self, user_id: str, application_ids: List[str]
    ) -> None:
        """Add applications to user. Does not delete existing."""
        unique_app_ids = list(set(application_ids))

        for app_id in unique_app_ids:
            # Check if already exists
            stmt = select(UserApplication).where(
                UserApplication.user_id == user_id,
                UserApplication.application_id == app_id,
            )
            result = await self.session.execute(stmt)
            if not result.scalar_one_or_none():
                user_app = UserApplication(user_id=user_id, application_id=app_id)
                self.session.add(user_app)

        await self.session.flush()

    async def add_application_to_user(self, user_id: str, application_id: str) -> None:
        """Add application to user, ignoring if already exists."""
        # Check if assignment already exists
        stmt = select(UserApplication).where(
            UserApplication.user_id == user_id,
            UserApplication.application_id == application_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Already assigned, skip
            return

        user_app = UserApplication(user_id=user_id, application_id=application_id)
        self.session.add(user_app)
        await self.session.flush()

    async def remove_application_from_user(
        self, user_id: str, application_id: str
    ) -> None:
        stmt = delete(UserApplication).where(
            UserApplication.user_id == user_id,
            UserApplication.application_id == application_id,
        )
        await self.session.execute(stmt)
        await self.session.flush()
