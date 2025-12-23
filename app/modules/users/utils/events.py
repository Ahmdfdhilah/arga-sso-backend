"""
User Event Utilities - Event publishing helpers
"""

from typing import Any, Dict, Optional
import logging
from datetime import datetime
import uuid

from app.modules.users.models.user import User
from app.core.messaging import EventPublisher, DomainEvent

logger = logging.getLogger(__name__)


class UserEventUtil:
    """Utility for publishing user events (aligned with HRIS EmployeeEventUtil)."""

    @staticmethod
    def to_event_data(user: User) -> Dict[str, Any]:
        """Convert user to event data payload."""
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "gender": user.gender,
            "avatar_path": user.avatar_path,
            "status": user.status,
            "role": user.role,
        }

    @staticmethod
    async def publish(
        event_publisher: Optional[EventPublisher], event_type: str, user: User
    ) -> None:
        """Publish user event using generic DomainEvent (HRIS pattern)."""
        if not event_publisher:
            return

        try:
            data = UserEventUtil.to_event_data(user)
            
            event = DomainEvent(
                event_type=f"user.{event_type}",
                entity_id=str(user.id),
                data=data,
            )
            
            await event_publisher.publish(event)
            logger.info(f"Published user.{event_type} for user {user.id}")
        except Exception as e:
            logger.warning(f"Failed to publish user.{event_type}: {e}")
