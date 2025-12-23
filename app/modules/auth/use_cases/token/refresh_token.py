"""Use case untuk refresh access token menggunakan refresh token."""

import logging
from typing import TYPE_CHECKING

from app.config.settings import settings
from app.core.security import TokenService
from app.core.exceptions import UnauthorizedException, NotFoundException
from app.modules.auth.schemas import RefreshResponse
from app.modules.auth.utils.token_helper import TokenHelper
from app.modules.users.repositories import UserQueries

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService

logger = logging.getLogger(__name__)


class RefreshTokenUseCase:
    """Use case untuk refresh access token menggunakan refresh token."""

    def __init__(
        self,
        user_queries: UserQueries,
        session_service: "SessionService",
    ):
        self.user_queries = user_queries
        self.session_service = session_service

    async def execute(
        self,
        refresh_token: str,
        device_id: str,
    ) -> RefreshResponse:
        """
        Refresh access token menggunakan refresh token.
        Validasi client_id dan device_id dari token payload.

        Args:
            refresh_token: Refresh token yang valid
            device_id: Device ID yang sesuai dengan session

        Returns:
            RefreshResponse dengan access token dan refresh token baru

        Raises:
            UnauthorizedException: Token tidak valid, device mismatch, atau session expired
            NotFoundException: User tidak ditemukan
        """
        logger.info("Token refresh attempt")

        # Verify refresh token
        payload = TokenService.verify_token(refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        client_id = payload.get("client_id") or "sso_portal"
        token_device_id = payload.get("device_id")

        if not user_id or not isinstance(user_id, str):
            raise UnauthorizedException("Invalid token payload: missing user_id")

        if token_device_id and token_device_id != device_id:
            raise UnauthorizedException("Device ID mismatch")

        # Validasi refresh token di session
        if not await self.session_service.validate_refresh_token(
            user_id=user_id,
            client_id=client_id,
            device_id=device_id,
            refresh_token=refresh_token,
        ):
            raise UnauthorizedException("Invalid refresh token or session expired")

        # Get user data
        user = await self.user_queries.get_by_id(user_id)
        if not user:
            raise NotFoundException("User tidak ditemukan")

        # Extract allowed apps
        allowed_apps, allowed_app_codes = TokenHelper.extract_allowed_apps_from_user(
            user
        )

        # Generate avatar signed URL
        from app.core.utils.file_upload import generate_signed_url_for_path
        avatar_url = (
            generate_signed_url_for_path(user.avatar_path) if user.avatar_path else None
        )

        # Create new tokens
        new_access_token = TokenService.create_access_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            email=user.email,
            avatar_url=avatar_url,
            extra_claims={
                "allowed_apps": allowed_app_codes,
                "client_id": client_id,
            },
        )
        new_refresh_token = TokenService.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            client_id=client_id,
            device_id=device_id,
        )

        # Update session dengan refresh token baru
        await self.session_service.update_session(
            user_id=user_id,
            client_id=client_id,
            device_id=device_id,
            refresh_token=new_refresh_token,
        )

        logger.info(
            f"Token refreshed untuk user {user_id}, client {client_id}, "
            f"device {device_id} dengan {len(allowed_apps)} allowed apps"
        )

        return RefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
