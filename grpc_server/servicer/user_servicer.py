import logging
from datetime import datetime
from typing import Optional

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy.ext.asyncio import AsyncSession

from proto.sso import user_pb2, user_pb2_grpc
from app.config.database import async_session_maker
from app.modules.users.repositories import UserQueries
from app.modules.users.models import User

logger = logging.getLogger(__name__)


def datetime_to_timestamp(dt: Optional[datetime]) -> Optional[Timestamp]:
    """Convert datetime to protobuf Timestamp."""
    if dt is None:
        return None
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


def user_to_proto(user: User) -> user_pb2.User:
    """Convert User model to protobuf User message."""
    proto_user = user_pb2.User(
        id=str(user.id),
        name=user.name,
        email=user.email or "",
        phone=user.phone or "",
        avatar_path=user.avatar_path or "",
        status=user.status,
        role=user.role,
        created_at=datetime_to_timestamp(user.created_at),
        updated_at=datetime_to_timestamp(user.updated_at),
        # Extended profile fields
        alias=user.alias or "",
        gender=user.gender or "",
        address=user.address or "",
        bio=user.bio or "",
    )
    
    # Handle optional date_of_birth timestamp
    if user.date_of_birth:
        proto_user.date_of_birth.CopyFrom(datetime_to_timestamp(user.date_of_birth))
    
    return proto_user


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
                user=user_to_proto(user),
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
                user=user_to_proto(user),
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
                user=user_to_proto(user),
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
                    users.append(user_to_proto(user))

        return user_pb2.BatchGetUsersResponse(users=users)
