
import asyncio
import logging
from typing import Optional
import aio_pika
from aio_pika import ExchangeType
from aio_pika.abc import AbstractChannel, AbstractConnection

from app.config.settings import settings

logger = logging.getLogger(__name__)

class MessageEngine:
    """
    Core engine for RabbitMQ connectivity and setup (SSO Backend).
    Singleton pattern.
    """
    _instance = None
    
    # SSO Specific DLX Config
    DLX_EXCHANGE = "sso.dlx"
    DLQ_QUEUE = "sso.dlq"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._connection: Optional[AbstractConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._lock = asyncio.Lock()
        self._connected = False
        self._initialized = True

    @property
    def is_connected(self) -> bool:
        return self._connected and self._connection is not None and not self._connection.is_closed

    async def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        if self.is_connected:
            return

        async with self._lock:
            if self.is_connected:
                return

            try:
                logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
                
                self._connection = await aio_pika.connect_robust(
                    host=settings.RABBITMQ_HOST,
                    port=settings.RABBITMQ_PORT,
                    login=settings.RABBITMQ_USER,
                    password=settings.RABBITMQ_PASSWORD,
                    virtualhost=settings.RABBITMQ_VHOST,
                )
                
                self._channel = await self._connection.channel()
                await self._channel.set_qos(prefetch_count=10)
                
                self._connected = True
                logger.info("RabbitMQ connection established")
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                self._connected = False
                raise

    async def disconnect(self) -> None:
        """Close RabbitMQ connection"""
        async with self._lock:
            if self._channel and not self._channel.is_closed:
                await self._channel.close()
            
            if self._connection and not self._connection.is_closed:
                await self._connection.close()
            
            self._connection = None
            self._channel = None
            self._connected = False
            logger.info("RabbitMQ connection closed")

    async def get_channel(self) -> AbstractChannel:
        if not self.is_connected:
            await self.connect()
        return self._channel

    async def apply_dlx(self) -> None:
        """
        Setup only DLX/DLQ config for SSO.
        SSO is primarily a Publisher, so it may not strictly need complex listener topology,
        but it MUST ensure its DLX exists for safety.
        """
        if not self.is_connected:
            await self.connect()
            
        channel = await self.get_channel()
        
        # 1. Setup DLX
        dlx = await channel.declare_exchange(
            self.DLX_EXCHANGE, ExchangeType.DIRECT, durable=True
        )
        dlq = await channel.declare_queue(self.DLQ_QUEUE, durable=True)
        await dlq.bind(dlx, routing_key="dead-letter")
        
        logger.info(f"SSO Topology applied: DLX={self.DLX_EXCHANGE}, DLQ={self.DLQ_QUEUE}")

# Global Instance
message_engine = MessageEngine()
