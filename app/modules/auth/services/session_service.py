import json
import uuid
import hashlib
from typing import Optional, Dict, Any, List
# from app.core.exceptions import BadRequestException

import redis.asyncio as redis

from app.config.settings import settings
from app.core.utils import get_utc_now


class SessionService:
    SESSION_PREFIX = "session"
    CLIENT_SESSIONS_PREFIX = "client_sessions"
    USER_SESSIONS_PREFIX = "user_sessions"
    SESSION_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _session_key(self, user_id: str, client_id: str, device_id: str) -> str:
        """Session key: session:{user_id}:{client_id}:{device_id}"""
        return f"{self.SESSION_PREFIX}:{user_id}:{client_id}:{device_id}"

    def _client_sessions_key(self, user_id: str, client_id: str) -> str:
        """Track all device sessions per client: client_sessions:{user_id}:{client_id}"""
        return f"{self.CLIENT_SESSIONS_PREFIX}:{user_id}:{client_id}"

    def _user_sessions_key(self, user_id: str) -> str:
        """Track all sessions (all clients): user_sessions:{user_id}"""
        return f"{self.USER_SESSIONS_PREFIX}:{user_id}"

    async def create_session(
        self,
        user_id: str,
        client_id: str,
        refresh_token: str,
        single_session: bool = False,
        device_id: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> str:
        """
        Create session for user in specific client application.

        Args:
            user_id: User UUID
            client_id: Application client code
            refresh_token: Refresh token to hash and store
            single_session: If True, delete all existing sessions for this client
            device_id: Optional device ID (auto-generated if not provided)
            device_info: Optional device metadata
            ip_address: Optional IP address
            fcm_token: Optional FCM token for push notifications

        Returns:
            device_id: UUID of the created session
        """
        
        # if not device_id:
        #     raise BadRequestException("Device ID dibutuhkan.")

        existing_sessions = await self.get_client_sessions(user_id, client_id)
        
        # Cek apakah device ini sudah punya session
        existing_device_ids = [s.get("device_id") for s in existing_sessions]
        is_same_device = device_id in existing_device_ids

        if single_session:
            if len(existing_sessions) > 0 and not is_same_device:
                from app.core.exceptions import BadRequestException
                raise BadRequestException("Anda sudah login di perangkat lain. Silakan logout terlebih dahulu.")
            elif is_same_device:
                await self.delete_client_device_session(user_id, client_id, device_id)

        if not single_session and len(existing_sessions) >= settings.MAX_ACTIVE_SESSIONS:
            # if not is_same_device:
            #     from app.core.exceptions import BadRequestException
            #     raise BadRequestException(f"Batas maksimum sesi tercapai ({settings.MAX_ACTIVE_SESSIONS}). Silakan logout dari perangkat lain.")
            # else:
            await self.delete_client_device_session(user_id, client_id, device_id)

        session_data = {
            "user_id": user_id,
            "client_id": client_id,
            "device_id": device_id,
            "refresh_token_hash": self._hash_token(refresh_token),
            "device_info": device_info or {},
            "ip_address": ip_address,
            "fcm_token": fcm_token,
            "created_at": get_utc_now().isoformat(),
            "last_activity": get_utc_now().isoformat(),
        }

        session_key = self._session_key(user_id, client_id, device_id)
        await self.redis.setex(
            session_key,
            self.SESSION_TTL,
            json.dumps(session_data),
        )

        client_sessions_key = self._client_sessions_key(user_id, client_id)
        await self.redis.sadd(client_sessions_key, device_id)  # type: ignore
        await self.redis.expire(client_sessions_key, self.SESSION_TTL)
        user_sessions_key = self._user_sessions_key(user_id)
        await self.redis.sadd(user_sessions_key, f"{client_id}:{device_id}")  # type: ignore
        await self.redis.expire(user_sessions_key, self.SESSION_TTL)

        return device_id

    async def get_session(
        self, user_id: str, client_id: str, device_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get session data for specific user, client, and device."""
        session_key = self._session_key(user_id, client_id, device_id)
        data = await self.redis.get(session_key)
        if data:
            return json.loads(data)
        return None

    async def validate_refresh_token(
        self, user_id: str, client_id: str, device_id: str, refresh_token: str
    ) -> bool:
        """Validate refresh token for specific session."""
        session = await self.get_session(user_id, client_id, device_id)
        if not session:
            return False
        return session.get("refresh_token_hash") == self._hash_token(refresh_token)

    async def update_session(
        self,
        user_id: str,
        client_id: str,
        device_id: str,
        refresh_token: Optional[str] = None,
        fcm_token: Optional[str] = None,
    ) -> bool:
        """Update session with new refresh token or FCM token."""
        session = await self.get_session(user_id, client_id, device_id)
        if not session:
            return False

        session["last_activity"] = get_utc_now().isoformat()
        if refresh_token:
            session["refresh_token_hash"] = self._hash_token(refresh_token)
        if fcm_token:
            session["fcm_token"] = fcm_token

        session_key = self._session_key(user_id, client_id, device_id)
        await self.redis.setex(session_key, self.SESSION_TTL, json.dumps(session))
        return True

    async def delete_client_device_session(
        self, user_id: str, client_id: str, device_id: str
    ) -> bool:
        """Delete specific device session for a client."""
        session_key = self._session_key(user_id, client_id, device_id)
        client_sessions_key = self._client_sessions_key(user_id, client_id)
        user_sessions_key = self._user_sessions_key(user_id)

        await self.redis.delete(session_key)
        await self.redis.srem(client_sessions_key, device_id)  # type: ignore
        await self.redis.srem(user_sessions_key, f"{client_id}:{device_id}")  # type: ignore
        return True

    async def delete_client_sessions(self, user_id: str, client_id: str) -> int:
        """Delete all sessions for a specific client (all devices)."""
        client_sessions_key = self._client_sessions_key(user_id, client_id)
        device_ids = await self.redis.smembers(client_sessions_key)  # type: ignore

        deleted_count = 0
        for device_id in device_ids:
            session_key = self._session_key(user_id, client_id, device_id)
            await self.redis.delete(session_key)
            deleted_count += 1

            # Clean up from user_sessions
            user_sessions_key = self._user_sessions_key(user_id)
            await self.redis.srem(user_sessions_key, f"{client_id}:{device_id}")  # type: ignore

        await self.redis.delete(client_sessions_key)
        return deleted_count

    async def delete_all_sessions(self, user_id: str) -> int:
        """Delete all sessions for user (all clients, all devices)."""
        user_sessions_key = self._user_sessions_key(user_id)
        client_device_pairs = await self.redis.smembers(user_sessions_key)  # type: ignore

        deleted_count = 0
        for pair in client_device_pairs:
            # pair format: "client_id:device_id"
            try:
                client_id, device_id = pair.split(":", 1)
                session_key = self._session_key(user_id, client_id, device_id)
                await self.redis.delete(session_key)
                deleted_count += 1

                client_sessions_key = self._client_sessions_key(user_id, client_id)
                await self.redis.srem(client_sessions_key, device_id)  # type: ignore
            except ValueError:
                # Skip invalid format
                continue

        await self.redis.delete(user_sessions_key)
        return deleted_count

    async def get_client_sessions(
        self, user_id: str, client_id: str
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a specific client."""
        client_sessions_key = self._client_sessions_key(user_id, client_id)
        device_ids = await self.redis.smembers(client_sessions_key)  # type: ignore

        sessions = []
        for device_id in device_ids:
            session = await self.get_session(user_id, client_id, device_id)
            if session:
                sessions.append(session)

        return sessions

    async def get_all_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for user (all clients)."""
        user_sessions_key = self._user_sessions_key(user_id)
        client_device_pairs = await self.redis.smembers(user_sessions_key)  # type: ignore

        sessions = []
        for pair in client_device_pairs:
            # pair format: "client_id:device_id"
            try:
                client_id, device_id = pair.split(":", 1)
                session = await self.get_session(user_id, client_id, device_id)
                if session:
                    sessions.append(session)
            except ValueError:
                # Skip invalid format
                continue

        return sessions
