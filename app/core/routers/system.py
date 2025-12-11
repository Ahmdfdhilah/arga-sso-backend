"""
System and health check endpoints.
"""

from fastapi import APIRouter
from app.config.settings import settings

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint providing service information."""
    return {
        "service": settings.APP_NAME,
        "version": "2.0.0",
        "docs": "/docs" if settings.DEBUG else None,
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME}
