from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

from app.config.settings import settings
from app.core.exceptions import UnauthorizedException


class TokenService:
    @staticmethod
    def create_access_token(
        user_id: str,
        role: str,
        name: Optional[str] = None,
        extra_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": user_id,
            "role": role,
            "name": name,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
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
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
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
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},
            )
        except JWTError as e:
            raise UnauthorizedException(f"Invalid token: {str(e)}")
