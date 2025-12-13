"""
Event Publisher for SSO

Publishes domain events to RabbitMQ for other services to consume.
SSO is master for user profile data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from aio_pika import Message, DeliveryMode

from app.core.messaging.rabbitmq import rabbitmq_manager

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes domain events to RabbitMQ.
    
    All events include:
    - event_type: The type of event (e.g., "user.created")
    - entity_id: The ID of the affected entity
    - data: Event payload
    - timestamp: When the event occurred
    - source_service: "sso"
    - correlation_id: For distributed tracing
    - version: Schema version
    """
    
    SERVICE_NAME = "sso"
    
    async def _publish(
        self,
        event_type: str,
        entity_id: Any,
        data: Dict[str, Any],
        correlation_id: str = None,
    ) -> None:
        """
        Internal publish method.
        
        Args:
            event_type: Event type (e.g., "user.created")
            entity_id: ID of the entity
            data: Event payload
            correlation_id: Optional correlation ID for tracing
        """
        if not rabbitmq_manager.is_connected:
            logger.warning(f"RabbitMQ not connected, skipping event: {event_type}")
            return
        
        try:
            event = {
                "event_type": event_type,
                "entity_id": str(entity_id) if entity_id else None,
                "data": data,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source_service": self.SERVICE_NAME,
                "correlation_id": correlation_id or str(uuid4()),
                "version": 1,
            }
            
            message = Message(
                body=json.dumps(event, default=str).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
            )
            
            exchange = await rabbitmq_manager.get_exchange()
            await exchange.publish(
                message,
                routing_key=event_type,
            )
            
            logger.info(f"Published event: {event_type} for entity {entity_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            # Don't raise - events are fire-and-forget
    
    # =========================================
    # User Events
    # =========================================
    
    async def publish_user_created(
        self,
        user_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Publish user.created event"""
        await self._publish("user.created", user_id, data)
    
    async def publish_user_updated(
        self,
        user_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Publish user.updated event"""
        await self._publish("user.updated", user_id, data)
    
    async def publish_user_deleted(
        self,
        user_id: str,
        data: Dict[str, Any] = None,
    ) -> None:
        """Publish user.deleted event"""
        await self._publish("user.deleted", user_id, data or {})


# Global singleton instance
event_publisher = EventPublisher()
