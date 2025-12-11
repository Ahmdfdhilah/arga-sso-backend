import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlencode
import httpx

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException, BadRequestException

logger = logging.getLogger(__name__)


@dataclass
class GoogleUser:
    """Dataclass untuk menyimpan informasi user dari Google."""

    google_id: str
    email: str
    name: Optional[str]
    picture: Optional[str]
    email_verified: bool
    locale: Optional[str]


class OAuth2GoogleSecurityService:
    """
    Security service untuk OAuth2 Google authentication.
    Menangani token verification, user info retrieval, dan OAuth2 flow.
    """

    @classmethod
    def get_authorization_url(
        cls, redirect_uri: Optional[str] = None, state: Optional[str] = None
    ) -> str:
        """
        Generate Google OAuth2 authorization URL.

        Args:
            redirect_uri: URL untuk callback setelah user authorize
            state: Optional state parameter untuk CSRF protection

        Returns:
            Authorization URL untuk redirect user ke Google login
        """
        logger.info("Generating Google OAuth2 authorization URL")

        redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
        scopes = " ".join(settings.GOOGLE_OAUTH_SCOPES)

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scopes,
            "access_type": "offline",
            "prompt": "consent",
        }

        if state:
            params["state"] = state

        query_string = urlencode(params)
        auth_url = f"{settings.GOOGLE_AUTHORIZATION_ENDPOINT}?{query_string}"

        logger.debug(f"Generated authorization URL for redirect: {redirect_uri}")
        return auth_url

    @classmethod
    async def exchange_code_for_token(
        cls, code: str, redirect_uri: Optional[str] = None
    ) -> str:
        """
        Exchange authorization code untuk access token.

        Args:
            code: Authorization code dari Google
            redirect_uri: Redirect URI yang digunakan saat authorization request.
                         Harus sama persis dengan yang dikirim ke Google saat request auth.

        Returns:
            Access token dari Google

        Raises:
            BadRequestException: Jika gagal exchange code
        """
        logger.info("Exchanging authorization code for access token")

        redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.GOOGLE_TOKEN_ENDPOINT,
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    logger.error(f"Failed to exchange code: {response.text}")
                    raise BadRequestException("Gagal mendapatkan token dari Google")

                token_data = response.json()
                access_token = token_data.get("access_token")

                if not access_token:
                    logger.error("No access token in response")
                    raise BadRequestException("Token tidak valid dari Google")

                logger.info("Successfully exchanged code for access token")
                return access_token

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {str(e)}")
            raise BadRequestException(
                "Terjadi kesalahan saat berkomunikasi dengan Google"
            )
        except BadRequestException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {str(e)}")
            raise BadRequestException("Terjadi kesalahan saat proses login")

    @classmethod
    async def get_user_info(cls, access_token: str) -> GoogleUser:
        """
        Retrieve user info dari Google menggunakan access token.

        Args:
            access_token: Access token dari Google

        Returns:
            GoogleUser object dengan informasi user

        Raises:
            UnauthorizedException: Jika gagal get user info atau data tidak lengkap
        """
        logger.info("Retrieving user info from Google")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    settings.GOOGLE_USERINFO_ENDPOINT,
                    headers={"Authorization": f"Bearer {access_token}"},
                )

                if response.status_code != 200:
                    logger.error(f"Failed to get user info: {response.text}")
                    raise UnauthorizedException(
                        "Gagal mendapatkan informasi user dari Google"
                    )

                user_info = response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during user info retrieval: {str(e)}")
            raise UnauthorizedException(
                "Terjadi kesalahan saat mengambil data user dari Google"
            )
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during user info retrieval: {str(e)}")
            raise UnauthorizedException("Gagal memproses data user dari Google")

        google_id = user_info.get("id")
        email = user_info.get("email")

        if not google_id or not email:
            logger.error(f"Missing required fields in Google user info: {user_info}")
            raise UnauthorizedException("Data user dari Google tidak lengkap")

        google_user = GoogleUser(
            google_id=google_id,
            email=email,
            name=user_info.get("name"),
            picture=user_info.get("picture"),
            email_verified=user_info.get("verified_email", False),
            locale=user_info.get("locale"),
        )

        logger.info(f"Successfully retrieved user info for Google ID: {google_id}")
        return google_user

    @classmethod
    async def verify_and_get_user(
        cls, code: str, redirect_uri: Optional[str] = None
    ) -> GoogleUser:
        """
        Convenience method untuk verify code dan get user info dalam satu call.

        Args:
            code: Authorization code dari Google
            redirect_uri: Redirect URI yang digunakan saat authorization request

        Returns:
            GoogleUser object dengan informasi user

        Raises:
            BadRequestException: Jika gagal exchange code
            UnauthorizedException: Jika gagal get user info
        """
        logger.info("Verifying authorization code and retrieving user info")

        access_token = await cls.exchange_code_for_token(code, redirect_uri)
        google_user = await cls.get_user_info(access_token)

        return google_user
