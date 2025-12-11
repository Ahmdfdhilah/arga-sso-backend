import redis.asyncio as redis
from typing import AsyncGenerator, Optional

from app.config.settings import settings


redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=50,
)


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()


class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.Redis(connection_pool=redis_pool)
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.aclose()
            cls._client = None
