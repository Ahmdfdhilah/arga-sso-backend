from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.config import get_db, get_redis
from app.modules.auth.repositories import AuthProviderQueries, AuthProviderCommands
from app.modules.auth.services import (
    SessionService,
    SSOSessionService,
    AuthService,
    EmailAuthService,
    FirebaseAuthService,
    OAuth2GoogleService,
)
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)


def get_auth_queries(db: AsyncSession = Depends(get_db)) -> AuthProviderQueries:
    return AuthProviderQueries(db)


def get_auth_commands(db: AsyncSession = Depends(get_db)) -> AuthProviderCommands:
    return AuthProviderCommands(db)


def get_user_queries(db: AsyncSession = Depends(get_db)) -> UserQueries:
    return UserQueries(db)


def get_user_commands(db: AsyncSession = Depends(get_db)) -> UserCommands:
    return UserCommands(db)


def get_app_queries(db: AsyncSession = Depends(get_db)) -> ApplicationQueries:
    return ApplicationQueries(db)


def get_session_service(
    redis_client: redis.Redis = Depends(get_redis),
) -> SessionService:
    return SessionService(redis_client)


def get_sso_session_service(
    redis_client: redis.Redis = Depends(get_redis),
) -> SSOSessionService:
    return SSOSessionService(redis_client)


def get_auth_service(
    user_queries: UserQueries = Depends(get_user_queries),
    auth_queries: AuthProviderQueries = Depends(get_auth_queries),
    session_service: SessionService = Depends(get_session_service),
    sso_session_service: SSOSessionService = Depends(get_sso_session_service),
    app_queries: ApplicationQueries = Depends(get_app_queries),
) -> AuthService:
    return AuthService(
        user_queries=user_queries,
        auth_queries=auth_queries,
        session_service=session_service,
        sso_session_service=sso_session_service,
        app_queries=app_queries,
    )


def get_email_auth_service(
    auth_queries: AuthProviderQueries = Depends(get_auth_queries),
    auth_commands: AuthProviderCommands = Depends(get_auth_commands),
    user_queries: UserQueries = Depends(get_user_queries),
    session_service: SessionService = Depends(get_session_service),
    sso_session_service: SSOSessionService = Depends(get_sso_session_service),
    app_queries: ApplicationQueries = Depends(get_app_queries),
) -> EmailAuthService:
    return EmailAuthService(
        auth_queries=auth_queries,
        auth_commands=auth_commands,
        user_queries=user_queries,
        session_service=session_service,
        sso_session_service=sso_session_service,
        app_queries=app_queries,
    )


def get_firebase_auth_service(
    auth_queries: AuthProviderQueries = Depends(get_auth_queries),
    auth_commands: AuthProviderCommands = Depends(get_auth_commands),
    user_queries: UserQueries = Depends(get_user_queries),
    user_commands: UserCommands = Depends(get_user_commands),
    session_service: SessionService = Depends(get_session_service),
    sso_session_service: SSOSessionService = Depends(get_sso_session_service),
    app_queries: ApplicationQueries = Depends(get_app_queries),
) -> FirebaseAuthService:
    return FirebaseAuthService(
        auth_queries=auth_queries,
        auth_commands=auth_commands,
        user_queries=user_queries,
        user_commands=user_commands,
        session_service=session_service,
        sso_session_service=sso_session_service,
        app_queries=app_queries,
    )


def get_oauth_google_service(
    auth_queries: AuthProviderQueries = Depends(get_auth_queries),
    auth_commands: AuthProviderCommands = Depends(get_auth_commands),
    user_queries: UserQueries = Depends(get_user_queries),
    user_commands: UserCommands = Depends(get_user_commands),
    session_service: SessionService = Depends(get_session_service),
    sso_session_service: SSOSessionService = Depends(get_sso_session_service),
    app_queries: ApplicationQueries = Depends(get_app_queries),
) -> OAuth2GoogleService:
    return OAuth2GoogleService(
        auth_queries=auth_queries,
        auth_commands=auth_commands,
        user_queries=user_queries,
        user_commands=user_commands,
        session_service=session_service,
        sso_session_service=sso_session_service,
        app_queries=app_queries,
    )


AuthQueriesDep = Annotated[AuthProviderQueries, Depends(get_auth_queries)]
AuthCommandsDep = Annotated[AuthProviderCommands, Depends(get_auth_commands)]
UserQueriesDep = Annotated[UserQueries, Depends(get_user_queries)]
SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
SSOSessionServiceDep = Annotated[SSOSessionService, Depends(get_sso_session_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
EmailAuthServiceDep = Annotated[EmailAuthService, Depends(get_email_auth_service)]
FirebaseAuthServiceDep = Annotated[
    FirebaseAuthService, Depends(get_firebase_auth_service)
]
OAuth2GoogleServiceDep = Annotated[
    OAuth2GoogleService, Depends(get_oauth_google_service)
]
