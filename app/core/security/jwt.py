from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException


def _load_private_key() -> str:
    with open(settings.JWT_PRIVATE_KEY_PATH, "r") as f:
        return f.read()


def _load_public_key() -> str:
    with open(settings.JWT_PUBLIC_KEY_PATH, "r") as f:
        return f.read()


class TokenService:
    _private_key: Optional[str] = None
    _public_key: Optional[str] = None

    @classmethod
    def get_private_key(cls) -> str:
        if cls._private_key is None:
            cls._private_key = _load_private_key()
        return cls._private_key

    @classmethod
    def get_public_key(cls) -> str:
        if cls._public_key is None:
            cls._public_key = _load_public_key()
        return cls._public_key

    @staticmethod
    def create_access_token(
        user_id: str,
        role: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id,
            "role": role,
            "name": name,
            "email": email,
            "avatar_url": avatar_url,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(
            payload, TokenService.get_private_key(), algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def create_refresh_token(
        user_id: str,
        role: str,
        name: Optional[str] = None,
        client_id: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> str:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": user_id,
            "role": role,
            "name": name,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        if client_id:
            payload["client_id"] = client_id
        if device_id:
            payload["device_id"] = device_id
        return jwt.encode(
            payload, TokenService.get_private_key(), algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token, TokenService.get_public_key(), algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != token_type:
                raise UnauthorizedException(
                    f"Invalid token type, expected {token_type}"
                )
            return payload
        except JWTError as e:
            raise UnauthorizedException(f"Invalid token: {str(e)}")

    @staticmethod
    def decode_token_without_verification(token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(
                token,
                TokenService.get_public_key(),
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},
            )
        except JWTError as e:
            raise UnauthorizedException(f"Invalid token: {str(e)}")

