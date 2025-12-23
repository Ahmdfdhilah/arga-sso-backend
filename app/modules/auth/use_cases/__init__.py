"""Auth use cases."""

from app.modules.auth.use_cases.token import (
    ExchangeSSOTokenUseCase,
    RefreshTokenUseCase,
    VerifyAccessTokenUseCase,
)
from app.modules.auth.use_cases.logout import (
    LogoutAllUseCase,
    LogoutSSOUseCase,
    LogoutClientUseCase,
    LogoutClientDeviceUseCase,
)
from app.modules.auth.use_cases.email import EmailLoginUseCase
from app.modules.auth.use_cases.firebase import FirebaseLoginUseCase
from app.modules.auth.use_cases.google import (
    GoogleOAuthGetAuthorizationURLUseCase,
    GoogleOAuthHandleCallbackUseCase,
)

__all__ = [
    # Token use cases
    "ExchangeSSOTokenUseCase",
    "RefreshTokenUseCase",
    "VerifyAccessTokenUseCase",
    # Logout use cases
    "LogoutAllUseCase",
    "LogoutSSOUseCase",
    "LogoutClientUseCase",
    "LogoutClientDeviceUseCase",
    # Authentication use cases
    "EmailLoginUseCase",
    "FirebaseLoginUseCase",
    "GoogleOAuthGetAuthorizationURLUseCase",
    "GoogleOAuthHandleCallbackUseCase",
]
