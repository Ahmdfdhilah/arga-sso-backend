import json
import uuid
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

import redis.asyncio as redis

from app.config.settings import settings
from app.core.utils import get_utc_now


class SSOSessionService:
    """
    Service for managing global SSO sessions.

    SSO session is created once during login and can be used to
    exchange for app-specific tokens without re-authentication.
    """

    SSO_PREFIX = "sso"
    SSO_TTL = 30 * 24 * 60 * 60  # 30 days

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    @staticmethod
    def _generate_sso_token() -> str:
        """Generate a secure random SSO token."""
        return str(uuid.uuid4())

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _sso_key(self, user_id: str) -> str:
        """Redis key for SSO session: sso:{user_id}"""
        return f"{self.SSO_PREFIX}:{user_id}"

    def _sso_token_key(self, token_hash: str) -> str:
        """Redis key for token lookup: sso_token:{token_hash}"""
        return f"sso_token:{token_hash}"

    async def create_sso_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
    ) -> str:
        """
        Create or refresh global SSO session for user.

        Args:
            user_id: User UUID string
            ip_address: Optional IP address

        Returns:
            sso_token: Token to be stored by client for session exchange
        """
        # Check if user already has SSO session
        existing = await self.get_sso_session_by_user(user_id)
        if existing:
            # Refresh existing session TTL and return existing token
            # We need to generate new token since we don't store plain token
            await self._delete_sso_session_internal(user_id)

        # Generate new SSO token
        sso_token = self._generate_sso_token()
        token_hash = self._hash_token(sso_token)

        session_data = {
            "user_id": user_id,
            "token_hash": token_hash,
            "ip_address": ip_address,
            "created_at": get_utc_now().isoformat(),
            "last_activity": get_utc_now().isoformat(),
        }

        # Store session by user_id
        sso_key = self._sso_key(user_id)
        await self.redis.setex(sso_key, self.SSO_TTL, json.dumps(session_data))

        # Store token lookup (token_hash -> user_id)
        token_key = self._sso_token_key(token_hash)
        await self.redis.setex(token_key, self.SSO_TTL, user_id)

        return sso_token

    async def validate_sso_token(self, sso_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate SSO token and return session data.

        Args:
            sso_token: The SSO token to validate

        Returns:
            Session data dict if valid, None if invalid/expired
        """
        token_hash = self._hash_token(sso_token)
        token_key = self._sso_token_key(token_hash)

        # Lookup user_id by token
        user_id = await self.redis.get(token_key)
        if not user_id:
            return None

        # Get session data
        if isinstance(user_id, bytes):
            user_id = user_id.decode()

        session = await self.get_sso_session_by_user(user_id)
        if not session:
            return None

        # Verify token hash matches
        if session.get("token_hash") != token_hash:
            return None

        # Update last activity
        await self._update_last_activity(user_id, session)

        return session

    async def get_sso_session_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get SSO session data by user_id."""
        sso_key = self._sso_key(user_id)
        data = await self.redis.get(sso_key)
        if data:
            if isinstance(data, bytes):
                data = data.decode()
            return json.loads(data)
        return None

    async def _update_last_activity(
        self, user_id: str, session: Dict[str, Any]
    ) -> None:
        """Update last activity timestamp."""
        session["last_activity"] = get_utc_now().isoformat()
        sso_key = self._sso_key(user_id)

        # Get remaining TTL
        ttl = await self.redis.ttl(sso_key)
        if ttl > 0:
            await self.redis.setex(sso_key, ttl, json.dumps(session))

    async def _delete_sso_session_internal(self, user_id: str) -> None:
        """Internal method to delete SSO session."""
        session = await self.get_sso_session_by_user(user_id)
        if session:
            # Delete token lookup
            token_hash = session.get("token_hash")
            if token_hash:
                token_key = self._sso_token_key(token_hash)
                await self.redis.delete(token_key)

        # Delete session
        sso_key = self._sso_key(user_id)
        await self.redis.delete(sso_key)

    async def delete_sso_session(self, user_id: str) -> bool:
        """
        Delete SSO session (global logout).
        This invalidates the SSO token but does NOT delete app sessions.

        Args:
            user_id: User UUID string

        Returns:
            True if session was deleted, False if not found
        """
        session = await self.get_sso_session_by_user(user_id)
        if not session:
            return False

        await self._delete_sso_session_internal(user_id)
        return True

    async def refresh_sso_session(self, sso_token: str) -> Optional[str]:
        """
        Refresh SSO session - generate new token and extend TTL.

        Args:
            sso_token: Current SSO token

        Returns:
            New SSO token if valid, None if session not found
        """
        session = await self.validate_sso_token(sso_token)
        if not session:
            return None

        user_id = session["user_id"]
        ip_address = session.get("ip_address")

        # Create new session (this deletes old and creates new)
        return await self.create_sso_session(user_id, ip_address)
