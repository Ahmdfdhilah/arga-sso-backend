"""
Messaging Infrastructure for SSO

Provides RabbitMQ connection management and event publishing.
"""

from app.core.messaging.rabbitmq import rabbitmq_manager, RabbitMQManager
from app.core.messaging.event_publisher import event_publisher, EventPublisher

__all__ = [
    "rabbitmq_manager",
    "RabbitMQManager", 
    "event_publisher",
    "EventPublisher",
]
