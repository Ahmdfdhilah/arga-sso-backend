"""
User Converters

Server-side: Convert User model to protobuf message.
"""

from proto.sso import user_pb2
from app.modules.users.models import User
from app.grpc.utils import datetime_to_timestamp


def user_to_proto(user: User) -> user_pb2.User:
    """Convert User model to protobuf User message."""
    return user_pb2.User(
        id=str(user.id),
        name=user.name,
        email=user.email or "",
        phone=user.phone or "",
        avatar_path=user.avatar_path or "",
        status=user.status,
        role=user.role,
        created_at=datetime_to_timestamp(user.created_at),
        updated_at=datetime_to_timestamp(user.updated_at),
    )
