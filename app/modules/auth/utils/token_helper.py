import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING

from app.config.settings import settings
from app.core.security import TokenService
from app.modules.auth.schemas.responses import LoginResponse, UserData, AllowedApp
from app.modules.users.models.user import User

if TYPE_CHECKING:
    from app.modules.auth.services.session_service import SessionService
    from app.modules.auth.services.sso_session_service import SSOSessionService

from app.core.utils.file_upload import generate_signed_url_for_path

logger = logging.getLogger(__name__)


class TokenHelper:
    def __init__(
        self,
        session_service: "SessionService",
        sso_session_service: "SSOSessionService",
    ):
        self.session_service = session_service
        self.sso_session_service = sso_session_service

    @staticmethod
    def extract_allowed_apps_from_user(
        user: User,
    ) -> tuple[List[AllowedApp], List[str]]:
        """Extract allowed apps from user model."""
        allowed_apps = []
        allowed_app_codes = []
        if user.applications:
            for app in user.applications:
                if app.is_active:
                    allowed_apps.append(
                        AllowedApp(
                            id=str(app.id),
                            code=app.code,
                            name=app.name
                        )
                    )
                    allowed_app_codes.append(app.code)  
        return allowed_apps, allowed_app_codes

    async def create_login_response(
        self,
        user: User,
        client_id: Optional[str] = None,
        single_session: bool = False,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """Create login response with tokens and session."""
        allowed_apps, allowed_app_codes = self.extract_allowed_apps_from_user(user)

        sso_token = await self.sso_session_service.create_sso_session(
            user_id=str(user.id),
            ip_address=ip_address,
        )
        avatar_url = generate_signed_url_for_path(user.avatar_path) if user.avatar_path else None
        
        user_data = UserData(
            id=str(user.id),
            role=user.role,
            name=user.name,
            email=user.email,
            avatar_url=avatar_url,
            allowed_apps=allowed_apps,
        )

        # SSO-only login (no client_id)
        # Only create SSO token, no need for app session
        if client_id is None:
            access_token = TokenService.create_access_token(
                user_id=str(user.id),
                role=user.role,
                name=user.name,
                extra_claims={"allowed_apps": allowed_app_codes},
            )

            # Create minimal refresh token for SSO frontend (no client_id, no device_id)
            refresh_token = TokenService.create_refresh_token(
                user_id=str(user.id),
                role=user.role,
                name=user.name,
            )

            logger.info(f"SSO login: {user.id} ({len(allowed_apps)} apps)")

            return LoginResponse(
                sso_token=sso_token,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=user_data,
            )

        # App-specific login
        access_token = TokenService.create_access_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            extra_claims={"allowed_apps": allowed_app_codes, "client_id": client_id},
        )

        refresh_token = TokenService.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            client_id=client_id,
        )

        device_id = await self.session_service.create_session(
            user_id=str(user.id),
            client_id=client_id,
            refresh_token=refresh_token,
            single_session=single_session,
            device_id=device_id,
            device_info=device_info,
            ip_address=ip_address,
            fcm_token=fcm_token,
        )

        refresh_token = TokenService.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            client_id=client_id,
            device_id=device_id,
        )

        await self.session_service.update_session(
            user_id=str(user.id),
            client_id=client_id,
            device_id=device_id,
            refresh_token=refresh_token,
        )

        logger.info(f"App login: {user.id} -> {client_id}")

        return LoginResponse(
            sso_token=sso_token,
            access_token=access_token,
            refresh_token=refresh_token,
            device_id=device_id,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_data,
        )

    async def create_app_tokens_for_exchange(
        self,
        user: User,
        client_id: str,
        sso_token: str,
        single_session: bool = False,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> LoginResponse:
        """Create app tokens for SSO exchange (does not recreate SSO session)."""
        allowed_apps, allowed_app_codes = self.extract_allowed_apps_from_user(user)

        avatar_url = generate_signed_url_for_path(user.avatar_path) if user.avatar_path else None
        user_data = UserData(
            id=str(user.id),
            role=user.role,
            name=user.name,
            email=user.email,
            avatar_url=avatar_url,
            allowed_apps=allowed_apps,
        )

        access_token = TokenService.create_access_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            extra_claims={"allowed_apps": allowed_app_codes, "client_id": client_id},
        )

        refresh_token = TokenService.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            client_id=client_id,
        )

        device_id = await self.session_service.create_session(
            user_id=str(user.id),
            client_id=client_id,
            refresh_token=refresh_token,
            single_session=single_session,
            device_id=device_id,
            device_info=device_info,
            ip_address=ip_address,
            fcm_token=fcm_token,
        )

        refresh_token = TokenService.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
            name=user.name,
            client_id=client_id,
            device_id=device_id,
        )

        await self.session_service.update_session(
            user_id=str(user.id),
            client_id=client_id,
            device_id=device_id,
            refresh_token=refresh_token,
        )

        logger.info(f"Token exchange: {user.id} -> {client_id}")

        return LoginResponse(
            sso_token=sso_token,
            access_token=access_token,
            refresh_token=refresh_token,
            device_id=device_id,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_data,
        )
