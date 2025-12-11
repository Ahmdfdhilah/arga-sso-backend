import logging
from datetime import datetime
from typing import Optional

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy.ext.asyncio import AsyncSession

from grpc_server.generated.proto.sso import user_pb2, user_pb2_grpc
from app.config.database import async_session_maker
from app.modules.users.repositories import UserQueries
from app.core.security import TokenService
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


def datetime_to_timestamp(dt: datetime) -> Timestamp:
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


class UserServicer(user_pb2_grpc.UserServiceServicer):

    async def _get_session(self) -> AsyncSession:
        return async_session_maker()

    async def GetUser(
        self,
        request: user_pb2.GetUserRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.UserResponse:
        logger.info(f"gRPC GetUser called for user_id: {request.user_id}")

        async with await self._get_session() as session:
            user_queries = UserQueries(session)
            user = await user_queries.get_by_id(request.user_id)

            if not user:
                return user_pb2.UserResponse(found=False)

            return user_pb2.UserResponse(
                found=True,
                user=user_pb2.User(
                    id=str(user.id),
                    name=user.name,
                    email=user.email or "",
                    phone=user.phone or "",
                    avatar_path=user.avatar_path or "",
                    status=user.status,
                    role=user.role,
                    created_at=datetime_to_timestamp(user.created_at),
                    updated_at=datetime_to_timestamp(user.updated_at),
                ),
            )

    async def GetUserByEmail(
        self,
        request: user_pb2.GetUserByEmailRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.UserResponse:
        logger.info(f"gRPC GetUserByEmail called for email: {request.email}")

        async with await self._get_session() as session:
            user_queries = UserQueries(session)
            user = await user_queries.get_by_email(request.email)

            if not user:
                return user_pb2.UserResponse(found=False)

            return user_pb2.UserResponse(
                found=True,
                user=user_pb2.User(
                    id=str(user.id),
                    name=user.name,
                    email=user.email or "",
                    phone=user.phone or "",
                    avatar_path=user.avatar_path or "",
                    status=user.status,
                    role=user.role,
                    created_at=datetime_to_timestamp(user.created_at),
                    updated_at=datetime_to_timestamp(user.updated_at),
                ),
            )

    async def GetUserByPhone(
        self,
        request: user_pb2.GetUserByPhoneRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.UserResponse:
        logger.info(f"gRPC GetUserByPhone called for phone: {request.phone}")

        async with await self._get_session() as session:
            user_queries = UserQueries(session)
            user = await user_queries.get_by_phone(request.phone)

            if not user:
                return user_pb2.UserResponse(found=False)

            return user_pb2.UserResponse(
                found=True,
                user=user_pb2.User(
                    id=str(user.id),
                    name=user.name,
                    email=user.email or "",
                    phone=user.phone or "",
                    avatar_path=user.avatar_path or "",
                    status=user.status,
                    role=user.role,
                    created_at=datetime_to_timestamp(user.created_at),
                    updated_at=datetime_to_timestamp(user.updated_at),
                ),
            )

    async def BatchGetUsers(
        self,
        request: user_pb2.BatchGetUsersRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.BatchGetUsersResponse:
        logger.info(f"gRPC BatchGetUsers called for {len(request.user_ids)} users")

        users = []
        async with await self._get_session() as session:
            user_queries = UserQueries(session)

            for user_id in request.user_ids:
                user = await user_queries.get_by_id(user_id)
                if user:
                    users.append(
                        user_pb2.User(
                            id=str(user.id),
                            name=user.name,
                            email=user.email or "",
                            phone=user.phone or "",
                            avatar_path=user.avatar_path or "",
                            status=user.status,
                            role=user.role,
                            created_at=datetime_to_timestamp(user.created_at),
                            updated_at=datetime_to_timestamp(user.updated_at),
                        )
                    )

        return user_pb2.BatchGetUsersResponse(users=users)

    async def ValidateToken(
        self,
        request: user_pb2.ValidateTokenRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.ValidateTokenResponse:
        logger.info("gRPC ValidateToken called")

        try:
            payload = TokenService.verify_token(
                request.access_token, token_type="access"
            )
            user_id = payload.get("sub")

            if not user_id or not isinstance(user_id, str):
                return user_pb2.ValidateTokenResponse(
                    is_valid=False,
                    error="Invalid token payload",
                )

            async with await self._get_session() as session:
                user_queries = UserQueries(session)
                user = await user_queries.get_by_id(user_id)

                if not user:
                    return user_pb2.ValidateTokenResponse(
                        is_valid=False,
                        error="User not found",
                    )

                return user_pb2.ValidateTokenResponse(
                    is_valid=True,
                    user=user_pb2.User(
                        id=str(user.id),
                        name=user.name,
                        email=user.email or "",
                        phone=user.phone or "",
                        avatar_path=user.avatar_path or "",
                        status=user.status,
                        role=user.role,
                        created_at=datetime_to_timestamp(user.created_at),
                        updated_at=datetime_to_timestamp(user.updated_at),
                    ),
                )
        except UnauthorizedException as e:
            return user_pb2.ValidateTokenResponse(
                is_valid=False,
                error=str(e.message),
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return user_pb2.ValidateTokenResponse(
                is_valid=False,
                error="Token validation failed",
            )
