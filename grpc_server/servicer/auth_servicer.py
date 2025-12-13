import logging
from datetime import datetime
from typing import Optional, Dict, Any

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy.ext.asyncio import AsyncSession

from proto.sso import auth_pb2, auth_pb2_grpc
from app.config.database import async_session_maker
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.auth.repositories import AuthProviderQueries, AuthProviderCommands
from app.modules.auth.services import (
    AuthService,
    SessionService,
    SSOSessionService,
    EmailAuthService,
    FirebaseAuthService,
)
from app.modules.auth.schemas import FirebaseLoginRequest
from app.modules.applications.repositories.queries.application_queries import (
    ApplicationQueries,
)
from app.core.security import TokenService
from app.core.exceptions import UnauthorizedException, NotFoundException, ForbiddenException
from app.core.utils.file_upload import generate_signed_url_for_path
from app.config.redis import RedisClient

logger = logging.getLogger(__name__)


def datetime_to_timestamp(dt: Optional[datetime]) -> Optional[Timestamp]:
    """Convert datetime to protobuf Timestamp."""
    if dt is None:
        return None
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


def device_info_to_dict(device_info: auth_pb2.DeviceInfo) -> Optional[Dict[str, Any]]:
    """Convert protobuf DeviceInfo to dict."""
    if not device_info:
        return None
    
    result = {}
    if device_info.platform:
        result["platform"] = device_info.platform
    if device_info.device_name:
        result["device_name"] = device_info.device_name
    if device_info.os_version:
        result["os_version"] = device_info.os_version
    if device_info.app_version:
        result["app_version"] = device_info.app_version
    if device_info.extra:
        result["extra"] = dict(device_info.extra)
    
    return result if result else None


def dict_to_device_info(data: Optional[Dict[str, Any]]) -> Optional[auth_pb2.DeviceInfo]:
    """Convert dict to protobuf DeviceInfo."""
    if not data:
        return None
    
    return auth_pb2.DeviceInfo(
        platform=data.get("platform", ""),
        device_name=data.get("device_name", ""),
        os_version=data.get("os_version", ""),
        app_version=data.get("app_version", ""),
        extra=data.get("extra", {}),
    )


class AuthServicer(auth_pb2_grpc.AuthServiceServicer):
    """gRPC servicer for authentication operations."""

    async def _get_session(self) -> AsyncSession:
        return async_session_maker()

    async def _create_services(self, session: AsyncSession):
        """Create all required services with dependencies."""
        user_queries = UserQueries(session)
        user_commands = UserCommands(session)
        auth_queries = AuthProviderQueries(session)
        auth_commands = AuthProviderCommands(session)
        app_queries = ApplicationQueries(session)
        
        redis_client = await RedisClient.get_client()
        session_service = SessionService(redis_client)
        sso_session_service = SSOSessionService(redis_client)

        auth_service = AuthService(
            user_queries=user_queries,
            auth_queries=auth_queries,
            session_service=session_service,
            sso_session_service=sso_session_service,
            app_queries=app_queries,
        )

        email_auth_service = EmailAuthService(
            auth_queries=auth_queries,
            auth_commands=auth_commands,
            user_queries=user_queries,
            session_service=session_service,
            sso_session_service=sso_session_service,
            app_queries=app_queries,
        )

        firebase_auth_service = FirebaseAuthService(
            auth_queries=auth_queries,
            auth_commands=auth_commands,
            user_queries=user_queries,
            user_commands=user_commands,
            session_service=session_service,
            sso_session_service=sso_session_service,
            app_queries=app_queries,
        )

        return {
            "user_queries": user_queries,
            "auth_service": auth_service,
            "email_auth_service": email_auth_service,
            "firebase_auth_service": firebase_auth_service,
            "session_service": session_service,
        }

    def _user_to_proto(self, user) -> auth_pb2.UserData:
        """Convert user model to proto UserData."""
        allowed_apps = []
        if hasattr(user, "applications") and user.applications:
            for app in user.applications:
                allowed_apps.append(
                    auth_pb2.AllowedApp(
                        id=str(app.id),
                        code=app.code,
                        name=app.name,
                    )
                )

        avatar_url = None
        if hasattr(user, "avatar_path") and user.avatar_path:
            avatar_url = generate_signed_url_for_path(user.avatar_path)

        return auth_pb2.UserData(
            id=str(user.id),
            role=user.role,
            name=user.name or "",
            email=user.email or "",
            avatar_url=avatar_url or "",
            allowed_apps=allowed_apps,
        )

    def _login_result_to_proto(self, result) -> auth_pb2.LoginResponse:
        """Convert login result to proto LoginResponse."""
        user_data = auth_pb2.UserData(
            id=result.user.id,
            role=result.user.role,
            name=result.user.name or "",
            email=result.user.email or "",
            avatar_url=result.user.avatar_url or "",
            allowed_apps=[
                auth_pb2.AllowedApp(id=app.id, code=app.code, name=app.name)
                for app in result.user.allowed_apps
            ],
        )

        return auth_pb2.LoginResponse(
            success=True,
            sso_token=result.sso_token,
            access_token=result.access_token or "",
            refresh_token=result.refresh_token or "",
            token_type=result.token_type,
            expires_in=result.expires_in or 0,
            user=user_data,
        )

    async def ValidateToken(
        self,
        request: auth_pb2.ValidateTokenRequest,
        context: grpc.aio.ServicerContext,
    ) -> auth_pb2.ValidateTokenResponse:
        """Validate JWT access token and return user data."""
        logger.info("gRPC ValidateToken called")

        try:
            payload = TokenService.verify_token(
                request.access_token, token_type="access"
            )
            user_id = payload.get("sub")

            if not user_id or not isinstance(user_id, str):
                return auth_pb2.ValidateTokenResponse(
                    is_valid=False,
                    error="Invalid token payload",
                )

            async with await self._get_session() as session:
                user_queries = UserQueries(session)
                user = await user_queries.get_by_id(user_id)

                if not user:
                    return auth_pb2.ValidateTokenResponse(
                        is_valid=False,
                        error="User not found",
                    )

                return auth_pb2.ValidateTokenResponse(
                    is_valid=True,
                    user=self._user_to_proto(user),
                )

        except UnauthorizedException as e:
            return auth_pb2.ValidateTokenResponse(
                is_valid=False,
                error=str(e.message),
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return auth_pb2.ValidateTokenResponse(
                is_valid=False,
                error="Token validation failed",
            )

    async def LoginWithEmail(
        self,
        request: auth_pb2.EmailLoginRequest,
        context: grpc.aio.ServicerContext,
    ) -> auth_pb2.LoginResponse:
        """Login with email and password."""
        logger.info(f"gRPC LoginWithEmail called for: {request.email}")

        try:
            async with await self._get_session() as session:
                services = await self._create_services(session)
                
                result = await services["email_auth_service"].login(
                    email=request.email,
                    password=request.password,
                    client_id=request.client_id if request.client_id else None,
                    device_info=device_info_to_dict(request.device_info) if request.HasField("device_info") else None,
                    ip_address=request.ip_address if request.ip_address else None,
                    fcm_token=request.fcm_token if request.fcm_token else None,
                )

                await session.commit()
                return self._login_result_to_proto(result)

        except UnauthorizedException as e:
            return auth_pb2.LoginResponse(
                success=False,
                error=str(e.message),
                token_type="bearer",
            )
        except Exception as e:
            logger.error(f"Email login error: {e}")
            return auth_pb2.LoginResponse(
                success=False,
                error="Login failed",
                token_type="bearer",
            )

    async def LoginWithFirebase(
        self,
        request: auth_pb2.FirebaseLoginRequest,
        context: grpc.aio.ServicerContext,
    ) -> auth_pb2.LoginResponse:
        """Login with Firebase token."""
        logger.info("gRPC LoginWithFirebase called")

        try:
            async with await self._get_session() as session:
                services = await self._create_services(session)

                firebase_request = FirebaseLoginRequest(
                    firebase_token=request.firebase_token,
                    client_id=request.client_id if request.client_id else None,
                    device_info=device_info_to_dict(request.device_info) if request.HasField("device_info") else None,
                    fcm_token=request.fcm_token if request.fcm_token else None,
                )

                result = await services["firebase_auth_service"].login(
                    request=firebase_request,
                    ip_address=request.ip_address if request.ip_address else None,
                )

                await session.commit()
                return self._login_result_to_proto(result)

        except UnauthorizedException as e:
            return auth_pb2.LoginResponse(
                success=False,
                error=str(e.message),
                token_type="bearer",
            )
        except Exception as e:
            logger.error(f"Firebase login error: {e}")
            return auth_pb2.LoginResponse(
                success=False,
                error="Login failed",
                token_type="bearer",
            )

    async def RefreshToken(
        self,
        request: auth_pb2.RefreshTokenRequest,
        context: grpc.aio.ServicerContext,
    ) -> auth_pb2.RefreshResponse:
        """Refresh access token."""
        logger.info("gRPC RefreshToken called")

        try:
            async with await self._get_session() as session:
                services = await self._create_services(session)

                result = await services["auth_service"].refresh_token(
                    refresh_token=request.refresh_token,
                    device_id=request.device_id,
                )

                return auth_pb2.RefreshResponse(
                    success=True,
                    access_token=result.access_token,
                    refresh_token=result.refresh_token,
                    token_type=result.token_type,
                    expires_in=result.expires_in,
                )

        except UnauthorizedException as e:
            return auth_pb2.RefreshResponse(
                success=False,
                error=str(e.message),
                token_type="bearer",
            )
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return auth_pb2.RefreshResponse(
                success=False,
                error="Token refresh failed",
                token_type="bearer",
            )

    async def ExchangeSSOToken(
        self,
        request: auth_pb2.SSOExchangeRequest,
        context: grpc.aio.ServicerContext,
    ) -> auth_pb2.LoginResponse:
        """Exchange SSO token for app-specific tokens."""
        logger.info(f"gRPC ExchangeSSOToken called for client: {request.client_id}")

        try:
            async with await self._get_session() as session:
                services = await self._create_services(session)

                result = await services["auth_service"].exchange_sso_token(
                    sso_token=request.sso_token,
                    client_id=request.client_id,
                    device_info=device_info_to_dict(request.device_info) if request.HasField("device_info") else None,
                    ip_address=request.ip_address if request.ip_address else None,
                    fcm_token=request.fcm_token if request.fcm_token else None,
                )

                await session.commit()
                return self._login_result_to_proto(result)

        except (UnauthorizedException, ForbiddenException, NotFoundException) as e:
            return auth_pb2.LoginResponse(
                success=False,
                error=str(e.message),
                token_type="bearer",
            )
        except Exception as e:
            logger.error(f"SSO exchange error: {e}")
            return auth_pb2.LoginResponse(
                success=False,
                error="SSO exchange failed",
                token_type="bearer",
            )

    async def Logout(
        self,
        request: auth_pb2.LogoutRequest,
        context: grpc.aio.ServicerContext,
    ) -> auth_pb2.LogoutResponse:
        """Logout user."""
        logger.info(f"gRPC Logout called for user: {request.user_id}")

        try:
            async with await self._get_session() as session:
                services = await self._create_services(session)
                auth_service = services["auth_service"]

                if request.global_: # type: ignore
                    await auth_service.logout_all(request.user_id)
                    message = "Logged out from all clients and devices"
                elif request.client_id and request.device_id:
                    await auth_service.logout_client_device(
                        request.user_id, request.client_id, request.device_id
                    )
                    message = f"Logged out from {request.client_id} device {request.device_id}"
                elif request.client_id:
                    await auth_service.logout_client(request.user_id, request.client_id)
                    message = f"Logged out from {request.client_id}"
                else:
                    await auth_service.logout_all(request.user_id)
                    message = "Logged out from all clients and devices"

                return auth_pb2.LogoutResponse(
                    success=True,
                    message=message,
                )

        except Exception as e:
            logger.error(f"Logout error: {e}")
            return auth_pb2.LogoutResponse(
                success=False,
                error=str(e),
                message="Logout failed",
            )

    async def GetSessions(
        self,
        request: auth_pb2.GetSessionsRequest,
        context: grpc.aio.ServicerContext,
    ) -> auth_pb2.GetSessionsResponse:
        """Get all sessions for a user."""
        logger.info(f"gRPC GetSessions called for user: {request.user_id}")

        try:
            async with await self._get_session() as session:
                services = await self._create_services(session)
                session_service = services["session_service"]

                all_sessions = await session_service.get_all_sessions(request.user_id)

                proto_sessions = []
                clients = set()

                for sess in all_sessions:
                    clients.add(sess.get("client_id", "unknown"))

                    created_at = None
                    last_activity = None
                    
                    if sess.get("created_at"):
                        created_at = datetime_to_timestamp(sess["created_at"])
                    if sess.get("last_activity"):
                        last_activity = datetime_to_timestamp(sess["last_activity"])

                    proto_sessions.append(
                        auth_pb2.SessionInfo(
                            device_id=sess["device_id"],
                            device_info=dict_to_device_info(sess.get("device_info")),
                            ip_address=sess.get("ip_address", ""),
                            client_id=sess.get("client_id", "unknown"),
                            created_at=created_at,
                            last_activity=last_activity,
                        )
                    )

                return auth_pb2.GetSessionsResponse(
                    sessions=proto_sessions,
                    total_clients=len(clients),
                    total_sessions=len(proto_sessions),
                )

        except Exception as e:
            logger.error(f"GetSessions error: {e}")
            return auth_pb2.GetSessionsResponse(
                sessions=[],
                total_clients=0,
                total_sessions=0,
            )
