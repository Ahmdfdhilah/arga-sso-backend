
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

@dataclass
class DomainEvent:
    event_type: str
    data: Dict[str, Any]
    entity_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    version: int = 1
    source: str = "sso"  # Origin service

    @property
    def routing_key(self) -> str:
        return self.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "version": self.version,
            "source": self.source,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, body: Dict[str, Any]) -> "DomainEvent":
        """
        Parses a dictionary (RabbitMQ body) into a DomainEvent.
        Handles variations in field naming if any.
        """
        # Handle 'source_service' vs 'source'
        source = body.get("source") or body.get("source_service", "unknown")
        
        # Handle 'event_action' if strictly separated from entity (though we prefer full event_type like user.created)
        event_type_str = body.get("event_type", "unknown.unknown")
        
        return cls(
            event_id=body.get("event_id") or body.get("correlation_id", str(uuid4())),
            event_type=event_type_str,
            entity_id=body.get("entity_id") or body.get("id"), # fallback
            timestamp=body.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            version=body.get("version", 1),
            source=source,
            data=body.get("data", {}),
        )
