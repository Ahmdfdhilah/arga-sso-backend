"""
Centralized middleware configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.core.middleware.error_handler import ErrorHandlerMiddleware, LoggingMiddleware


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Middleware order: CORS -> Logging -> Error Handler
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(LoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
