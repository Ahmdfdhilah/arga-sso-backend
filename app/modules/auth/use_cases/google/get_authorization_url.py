"""Use case untuk generate Google OAuth2 authorization URL."""

from typing import Optional

from app.core.security import OAuth2GoogleSecurityService


class GoogleOAuthGetAuthorizationURLUseCase:
    """Use case untuk generate Google OAuth2 authorization URL."""

    def execute(
        self, redirect_uri: Optional[str] = None, state: Optional[str] = None
    ) -> str:
        """
        Generate Google OAuth2 authorization URL.

        Args:
            redirect_uri: Optional custom redirect URI
            state: Optional state parameter untuk CSRF protection

        Returns:
            Authorization URL string untuk redirect user ke Google
        """
        return OAuth2GoogleSecurityService.get_authorization_url(
            redirect_uri=redirect_uri, state=state
        )
