"""
Application lifespan management.
"""

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from app.config.settings import settings
from app.config.redis import RedisClient
from app.core.security.firebase import FirebaseService
from app.core.messaging.engine import message_engine
from app.grpc import grpc_server
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application startup and shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None: Control back to the application
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")

    if settings.FIREBASE_PROJECT_ID:
        try:
            FirebaseService.initialize()
        except Exception as e:
            logger.warning(f"Firebase initialization skipped: {e}")

    # Run DB Migrations
    if settings.RUN_MIGRATIONS:
        logger.info("Running database migrations...")
        try:
            import subprocess
            import sys
            
            def run_migration():
                result = subprocess.run(
                    [sys.executable, "-m", "alembic", "upgrade", "head"],
                    capture_output=True,
                    text=True,
                    cwd="."
                )
                if result.returncode != 0:
                    raise Exception(f"Migration failed: {result.stderr}")
                return result.stdout
            
            output = await asyncio.to_thread(run_migration)
            logger.info("Database migrations completed successfully.")
            if output:
                logger.debug(f"Migration output: {output}")
        except Exception as e:
            logger.error(f"Failed to run database migrations: {e}")
            raise e

    logger.info("Checking Redis connection...")
    try:
        redis = await RedisClient.get_client()
        await redis.ping()
        logger.info("Redis connection OK")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise RuntimeError(f"Cannot start: Redis unavailable - {e}")

    # RabbitMQ initialization
    try:
        await message_engine.connect()
        await message_engine.apply_dlx()
        logger.info("RabbitMQ initialized successfully (SSO Publisher)")
    except Exception as e:
        logger.warning(f"RabbitMQ initialization failed: {e}. Events will not be published.")

    # gRPC server initialization
    logger.info("Starting gRPC server...")
    try:
        await grpc_server.start()
        logger.info("gRPC server started successfully")
    except Exception as e:
        logger.warning(f"Failed to start gRPC server: {e}. gRPC calls will not work.")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")

    # Stop gRPC server
    logger.info("Stopping gRPC server...")
    await grpc_server.stop()
    logger.info("gRPC server stopped")
    
    # Disconnect RabbitMQ
    try:
        await message_engine.disconnect()
    except Exception as e:
        logger.warning(f"RabbitMQ disconnect error: {e}")
    
    await RedisClient.close()

