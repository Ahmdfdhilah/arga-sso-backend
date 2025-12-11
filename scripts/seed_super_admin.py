import asyncio
import logging
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

sys.path.insert(0, ".")

from app.config.database import async_session_maker, engine, Base
from app.config.settings import settings
from app.modules.applications.models.user_application import (
    UserApplication,
)  # noqa: F401 
from app.modules.users.models.user import User
from app.modules.auth.models.auth_provider import AuthProvider
from app.core.security.password import PasswordService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def create_tables():
    logger.info("Creating database tables if not exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")


async def seed_super_admin():
    logger.info("Starting super admin seeder...")

    async with async_session_maker() as session:
        logger.info(
            f"Checking if super admin exists with email: {settings.SUPERADMIN_EMAIL}"
        )

        result = await session.execute(
            select(AuthProvider).where(
                AuthProvider.provider == "email",
                AuthProvider.provider_user_id == settings.SUPERADMIN_EMAIL,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            logger.info("Super admin already exists, skipping creation")
            logger.info(f"Existing user ID: {existing.user_id}")
            return

        logger.info("Creating new super admin user...")

        now = datetime.now(timezone.utc)
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            name=settings.SUPERADMIN_NAME,
            email=settings.SUPERADMIN_EMAIL,
            phone=settings.SUPERADMIN_PHONE,
            status="active",
            role="superadmin",
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        logger.info(f"User created with ID: {user_id}")
        logger.info(f"User name: {settings.SUPERADMIN_NAME}")
        logger.info(f"User email: {settings.SUPERADMIN_EMAIL}")
        logger.info(f"User role: superadmin")

        logger.info("Hashing password...")
        password = settings.SUPERADMIN_PASSWORD[:72]
        password_hash = PasswordService.hash_password(password)
        logger.info("Password hashed successfully")

        logger.info("Creating auth provider for email login...")
        auth_provider = AuthProvider(
            user_id=user_id,
            provider="email",
            provider_user_id=settings.SUPERADMIN_EMAIL,
            password_hash=password_hash,
            last_used_at=now,
            created_at=now,
            updated_at=now,
        )
        session.add(auth_provider)
        logger.info("Auth provider created for email login")

        await session.commit()
        logger.info("Database commit successful")

        logger.info("=" * 50)
        logger.info("SUPER ADMIN CREATED SUCCESSFULLY")
        logger.info("=" * 50)
        logger.info(f"ID: {user_id}")
        logger.info(f"Name: {settings.SUPERADMIN_NAME}")
        logger.info(f"Email: {settings.SUPERADMIN_EMAIL}")
        logger.info(f"Role: superadmin")
        logger.info("=" * 50)


async def main():
    logger.info("=" * 50)
    logger.info("ARGA SSO V2 - SUPER ADMIN SEEDER")
    logger.info("=" * 50)

    try:
        await create_tables()
        await seed_super_admin()
        logger.info("Seeder completed successfully")
    except Exception as e:
        logger.error(f"Seeder failed with error: {e}")
        raise
    finally:
        await engine.dispose()
        logger.info("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
