import logging
from datetime import datetime
from typing import Optional

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy.ext.asyncio import AsyncSession

from proto.sso import user_pb2, user_pb2_grpc
from app.config.database import async_session_maker
from app.modules.users.repositories import UserQueries, UserCommands
from app.modules.auth.repositories import AuthProviderCommands
from app.modules.users.models import User
from app.core.enums import UserRole, UserStatus, AuthProvider
from app.core.security import PasswordService
from app.grpc.utils import datetime_to_timestamp, generate_temp_password
from app.grpc.converters import user_to_proto
from app.core.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)


class UserHandler(user_pb2_grpc.UserServiceServicer):

    async def _get_session(self) -> AsyncSession:
        return async_session_maker()

    async def GetUser(
        self,
        request: user_pb2.GetUserRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.UserResponse:
        logger.info(f"gRPC GetUser called for user_id: {request.user_id}")

        try:
            async with await self._get_session() as session:
                user_queries = UserQueries(session)
                user = await user_queries.get_by_id(request.user_id)

                if not user:
                    return user_pb2.UserResponse(found=False)

                return user_pb2.UserResponse(
                    found=True,
                    user=user_to_proto(user),
                )
        except Exception as e:
            logger.error(f"gRPC GetUser failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetUserByEmail(
        self,
        request: user_pb2.GetUserByEmailRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.UserResponse:
        logger.info(f"gRPC GetUserByEmail called for email: {request.email}")

        try:
            async with await self._get_session() as session:
                user_queries = UserQueries(session)
                user = await user_queries.get_by_email(request.email)

                if not user:
                    return user_pb2.UserResponse(found=False)

                return user_pb2.UserResponse(
                    found=True,
                    user=user_to_proto(user),
                )
        except Exception as e:
            logger.error(f"gRPC GetUserByEmail failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def GetUserByPhone(
        self,
        request: user_pb2.GetUserByPhoneRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.UserResponse:
        logger.info(f"gRPC GetUserByPhone called for phone: {request.phone}")

        try:
            async with await self._get_session() as session:
                user_queries = UserQueries(session)
                user = await user_queries.get_by_phone(request.phone)

                if not user:
                    return user_pb2.UserResponse(found=False)

                return user_pb2.UserResponse(
                    found=True,
                    user=user_to_proto(user),
                )
        except Exception as e:
            logger.error(f"gRPC GetUserByPhone failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def BatchGetUsers(
        self,
        request: user_pb2.BatchGetUsersRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.BatchGetUsersResponse:
        logger.info(f"gRPC BatchGetUsers called for {len(request.user_ids)} users")

        try:
            users = []
            async with await self._get_session() as session:
                user_queries = UserQueries(session)

                for user_id in request.user_ids:
                    user = await user_queries.get_by_id(user_id)
                    if user:
                        users.append(user_to_proto(user))

            return user_pb2.BatchGetUsersResponse(users=users)
        except Exception as e:
            logger.error(f"gRPC BatchGetUsers failed: {e}", exc_info=True)
            await context.abort(grpc.StatusCode.INTERNAL, str(e))

    async def CreateUser(
        self,
        request: user_pb2.CreateUserRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.CreateUserResponse:
        """Create user with optional email/password auth provider."""
        logger.info(f"gRPC CreateUser called for email: {request.email}")

        async with await self._get_session() as session:
            try:
                user_queries = UserQueries(session)
                user_commands = UserCommands(session)
                auth_commands = AuthProviderCommands(session)

                # Check if email already exists
                existing = await user_queries.get_by_email(request.email)
                if existing:
                    return user_pb2.CreateUserResponse(
                        success=False,
                        error=f"Email {request.email} sudah terdaftar"
                    )

                # Map role string to enum
                role = UserRole.USER
                if request.role:
                    try:
                        role = UserRole(request.role)
                    except ValueError:
                        role = UserRole.USER

                # Create user
                user = await user_commands.create(
                    name=request.name,
                    email=request.email,
                    phone=request.phone if request.phone else None,
                    role=role,
                    status=UserStatus.ACTIVE,
                )

                # Create email auth provider with password
                temp_password = None
                if request.password:
                    password = request.password
                else:
                    password = generate_temp_password()
                    temp_password = password

                password_hash = PasswordService.hash_password(password)
                await auth_commands.create(
                    user_id=user.id,
                    provider=AuthProvider.EMAIL.value,
                    provider_user_id=request.email,
                    password_hash=password_hash,
                )

                await session.commit()
                logger.info(f"User created via gRPC: {user.id}")

                return user_pb2.CreateUserResponse(
                    success=True,
                    user=user_to_proto(user),
                    temporary_password=temp_password,
                )

            except BadRequestException as e:
                await session.rollback()
                return user_pb2.CreateUserResponse(
                    success=False,
                    error=str(e)
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create user: {e}", exc_info=True)
                return user_pb2.CreateUserResponse(
                    success=False,
                    error=str(e)
                )

    async def UpdateUser(
        self,
        request: user_pb2.UpdateUserRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.UpdateUserResponse:
        """Update user profile."""
        logger.info(f"gRPC UpdateUser called for user_id: {request.user_id}")

        async with await self._get_session() as session:
            try:
                user_queries = UserQueries(session)

                user = await user_queries.get_by_id(request.user_id)
                if not user:
                    return user_pb2.UpdateUserResponse(
                        success=False,
                        error=f"User {request.user_id} tidak ditemukan"
                    )

                # Update fields if provided
                if request.name:
                    user.name = request.name
                if request.email:
                    user.email = request.email
                if request.phone:
                    user.phone = request.phone
                if request.role:
                    user.role = request.role
                if request.status:
                    user.status = request.status

                await session.flush()
                await session.commit()
                await session.refresh(user)

                logger.info(f"User updated via gRPC: {user.id}")

                return user_pb2.UpdateUserResponse(
                    success=True,
                    user=user_to_proto(user),
                )

            except NotFoundException as e:
                await session.rollback()
                return user_pb2.UpdateUserResponse(
                    success=False,
                    error=str(e)
                )
            except BadRequestException as e:
                await session.rollback()
                return user_pb2.UpdateUserResponse(
                    success=False,
                    error=str(e)
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update user: {e}", exc_info=True)
                return user_pb2.UpdateUserResponse(
                    success=False,
                    error=str(e)
                )

    async def DeleteUser(
        self,
        request: user_pb2.DeleteUserRequest,
        context: grpc.aio.ServicerContext,
    ) -> user_pb2.DeleteUserResponse:
        """Soft delete user."""
        logger.info(f"gRPC DeleteUser called for user_id: {request.user_id}")

        async with await self._get_session() as session:
            try:
                user_queries = UserQueries(session)
                user_commands = UserCommands(session)

                user = await user_queries.get_by_id(request.user_id)
                if not user:
                    return user_pb2.DeleteUserResponse(
                        success=False,
                        error=f"User {request.user_id} tidak ditemukan"
                    )

                await user_commands.delete(user)
                await session.commit()

                logger.info(f"User deleted via gRPC: {request.user_id}")

                return user_pb2.DeleteUserResponse(success=True)

            except NotFoundException as e:
                await session.rollback()
                return user_pb2.DeleteUserResponse(
                    success=False,
                    error=str(e)
                )
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to delete user: {e}", exc_info=True)
                return user_pb2.DeleteUserResponse(
                    success=False,
                    error=str(e)
                )

