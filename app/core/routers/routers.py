"""
Centralized router configuration.
"""

from typing import Sequence
from fastapi import FastAPI, APIRouter
from app.config.settings import settings
from app.modules.auth.routers import auth_router, jwks_router
from app.modules.users.routers import users_router
from app.modules.applications.routers import applications_router
from app.core.routers.system import router as system_router

def setup_routers(app: FastAPI) -> None:
    """
    Register all API routers to the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.include_router(system_router, tags=["System"])
    
    app.include_router(jwks_router)

    routers: Sequence[tuple[APIRouter, str, Sequence[str]]] = [
        (auth_router, "/auth", ("Authentication",)),
        (users_router, "/users", ("User Management",)),
        (applications_router, "/applications", ("Applications",)),
    ]

    for router, prefix, tags in routers:
        app.include_router(
            router, prefix=f"{settings.API_PREFIX}{prefix}", tags=list(tags)
        )

