import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.core.enums import UserRole, UserStatus

if TYPE_CHECKING:
    from app.modules.auth.models.auth_provider import AuthProvider
    from app.modules.applications.models.application import Application


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)
    avatar_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserStatus.ACTIVE.value
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=UserRole.USER.value
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    auth_providers: Mapped[list["AuthProvider"]] = relationship(
        "AuthProvider", back_populates="user", cascade="all, delete-orphan"
    )

    applications: Mapped[List["Application"]] = relationship(
        "Application",
        secondary="user_applications",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"
