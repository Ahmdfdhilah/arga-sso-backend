"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from app.config.settings import settings
from app.core.utils.logging import setup_logging
from app.core.utils.lifespan import lifespan
from app.core.middleware import setup_middleware
from app.core.routers import setup_routers

# Setup logging
setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="ARGA SSO Service with multi-method authentication",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Setup middleware
setup_middleware(app)

# Setup routers
setup_routers(app)
