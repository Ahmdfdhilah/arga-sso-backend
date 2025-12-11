import logging
from typing import Optional
from dataclasses import dataclass

import firebase_admin
from firebase_admin import auth, credentials

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


@dataclass
class FirebaseUser:
    uid: str
    email: Optional[str]
    name: Optional[str]
    phone: Optional[str]
    picture: Optional[str]
    email_verified: bool
    provider_id: str
    provider_data: dict


class FirebaseService:
    _initialized: bool = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return

        try:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise

    @classmethod
    async def verify_token(cls, id_token: str) -> FirebaseUser:
        if not cls._initialized:
            cls.initialize()

        try:
            decoded_token = auth.verify_id_token(id_token)

            firebase_info = decoded_token.get("firebase", {})
            sign_in_provider = firebase_info.get("sign_in_provider", "unknown")

            return FirebaseUser(
                uid=decoded_token["uid"],
                email=decoded_token.get("email"),
                name=decoded_token.get("name"),
                phone=decoded_token.get("phone_number"),
                picture=decoded_token.get("picture"),
                email_verified=decoded_token.get("email_verified", False),
                provider_id=sign_in_provider,
                provider_data=firebase_info,
            )
        except auth.InvalidIdTokenError as e:
            logger.warning(f"Invalid Firebase ID token: {e}")
            raise UnauthorizedException("Invalid Firebase token")
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise UnauthorizedException(f"Firebase authentication failed: {str(e)}")

    @classmethod
    async def get_user(cls, uid: str):
        if not cls._initialized:
            cls.initialize()

        try:
            return auth.get_user(uid)
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get Firebase user {uid}: {e}")
            raise
