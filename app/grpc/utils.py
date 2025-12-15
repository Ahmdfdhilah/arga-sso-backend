"""
gRPC Utility Functions for SSO Backend

Shared helpers for gRPC handlers.
"""

import secrets
import string
from datetime import datetime
from typing import Optional, Dict, Any

from google.protobuf.timestamp_pb2 import Timestamp
from proto.sso import auth_pb2


def datetime_to_timestamp(dt: Optional[datetime]) -> Optional[Timestamp]:
    """Convert datetime to protobuf Timestamp."""
    if dt is None:
        return None
    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


def device_info_to_dict(device_info: auth_pb2.DeviceInfo) -> Optional[Dict[str, Any]]:
    """Convert protobuf DeviceInfo to dict."""
    if not device_info:
        return None
    
    result = {}
    if device_info.platform:
        result["platform"] = device_info.platform
    if device_info.device_name:
        result["device_name"] = device_info.device_name
    if device_info.os_version:
        result["os_version"] = device_info.os_version
    if device_info.app_version:
        result["app_version"] = device_info.app_version
    if device_info.extra:
        result["extra"] = dict(device_info.extra)
    
    return result if result else None


def dict_to_device_info(data: Optional[Dict[str, Any]]) -> Optional[auth_pb2.DeviceInfo]:
    """Convert dict to protobuf DeviceInfo."""
    if not data:
        return None
    
    return auth_pb2.DeviceInfo(
        platform=data.get("platform", ""),
        device_name=data.get("device_name", ""),
        os_version=data.get("os_version", ""),
        app_version=data.get("app_version", ""),
        extra=data.get("extra", {}),
    )


def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
