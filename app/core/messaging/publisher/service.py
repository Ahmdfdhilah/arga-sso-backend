
import json
import logging
from typing import Any, Dict
from aio_pika import Message, DeliveryMode, ExchangeType

from app.core.messaging.engine import message_engine
from app.core.messaging.types import DomainEvent

logger = logging.getLogger(__name__)

class EventPublisher:
    """
    Standardized Event Publisher for SSO.
    Uses MessageEngine for channel access.
    """
    
    EXCHANGE_NAME = "sso.events"

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish a generic DomainEvent to the topic exchange.
        """
        try:
            channel = await message_engine.get_channel()
            
            exchange = await channel.declare_exchange(
                self.EXCHANGE_NAME, 
                ExchangeType.TOPIC, 
                durable=True
            )
            
            message = Message(
                body=json.dumps(event.to_dict(), default=str).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
                app_id="arga-sso-service",
                type=event.event_type
            )
            
            await exchange.publish(
                message,
                routing_key=event.routing_key,
            )
            
            logger.info(f"Published event: {event.event_type} [ID: {event.entity_id}]")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_type}: {e}")
    
    async def publish_user_created(self, user_id: str, data: Dict[str, Any]) -> None:
        event = DomainEvent(
            event_type="user.created",
            entity_id=user_id,
            data=data
        )
        await self.publish(event)

    async def publish_user_updated(self, user_id: str, data: Dict[str, Any]) -> None:
        event = DomainEvent(
            event_type="user.updated",
            entity_id=user_id,
            data=data
        )
        await self.publish(event)

    async def publish_user_deleted(self, user_id: str, data: Dict[str, Any] = None) -> None:
        event = DomainEvent(
            event_type="user.deleted",
            entity_id=user_id,
            data=data or {}
        )
        await self.publish(event)

# Global Instance
event_publisher = EventPublisher()
