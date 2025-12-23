"""Use case untuk verify JWT access token."""

import logging

from app.core.security import TokenService
from app.core.exceptions import UnauthorizedException
from app.modules.auth.schemas import UserData
from app.modules.auth.schemas.responses import AllowedApp

logger = logging.getLogger(__name__)


class VerifyAccessTokenUseCase:
    """Use case untuk verify dan extract data dari JWT access token."""

    async def execute(self, access_token: str) -> UserData:
        """
        Verify access token dan extract user data dari payload.

        Args:
            access_token: JWT access token yang akan diverify

        Returns:
            UserData dengan informasi user dari token payload

        Raises:
            UnauthorizedException: Token tidak valid atau payload tidak lengkap
        """
        # Verify token signature dan expiry
        payload = TokenService.verify_token(access_token, token_type="access")

        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not isinstance(user_id, str):
            raise UnauthorizedException("Invalid token payload: missing user id")
        if not role or not isinstance(role, str):
            raise UnauthorizedException("Invalid token payload: missing role")

        # Extract allowed_apps dari payload
        allowed_app_codes = payload.get("allowed_apps", [])
        allowed_apps = [
            AllowedApp(id="", code=code, name="") for code in allowed_app_codes
        ]

        return UserData(
            id=user_id,
            role=role,
            name=payload.get("name"),
            email=payload.get("email"),
            allowed_apps=allowed_apps,
        )
