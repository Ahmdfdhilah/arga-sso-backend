"""
Auth Converters

Server-side: Convert auth-related models to protobuf messages.
"""

from proto.sso import auth_pb2
from app.core.utils.file_upload import generate_signed_url_for_path


def user_to_auth_proto(user) -> auth_pb2.UserData:
    """Convert User model to protobuf auth UserData message."""
    allowed_apps = []
    if hasattr(user, "applications") and user.applications:
        for app in user.applications:
            allowed_apps.append(
                auth_pb2.AllowedApp(
                    id=str(app.id),
                    code=app.code,
                    name=app.name,
                )
            )

    avatar_url = None
    if hasattr(user, "avatar_path") and user.avatar_path:
        avatar_url = generate_signed_url_for_path(user.avatar_path)

    return auth_pb2.UserData(
        id=str(user.id),
        role=user.role,
        name=user.name or "",
        email=user.email or "",
        avatar_url=avatar_url or "",
        allowed_apps=allowed_apps,
    )


def login_result_to_proto(result) -> auth_pb2.LoginResponse:
    """Convert login result to proto LoginResponse."""
    user_data = auth_pb2.UserData(
        id=result.user.id,
        role=result.user.role,
        name=result.user.name or "",
        email=result.user.email or "",
        avatar_url=result.user.avatar_url or "",
        allowed_apps=[
            auth_pb2.AllowedApp(id=app.id, code=app.code, name=app.name)
            for app in result.user.allowed_apps
        ],
    )

    return auth_pb2.LoginResponse(
        success=True,
        sso_token=result.sso_token,
        access_token=result.access_token or "",
        refresh_token=result.refresh_token or "",
        token_type=result.token_type,
        expires_in=result.expires_in or 0,
        user=user_data,
    )
