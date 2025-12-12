from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DeviceInfo(_message.Message):
    __slots__ = ("platform", "device_name", "os_version", "app_version", "extra")
    class ExtraEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PLATFORM_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NAME_FIELD_NUMBER: _ClassVar[int]
    OS_VERSION_FIELD_NUMBER: _ClassVar[int]
    APP_VERSION_FIELD_NUMBER: _ClassVar[int]
    EXTRA_FIELD_NUMBER: _ClassVar[int]
    platform: str
    device_name: str
    os_version: str
    app_version: str
    extra: _containers.ScalarMap[str, str]
    def __init__(self, platform: _Optional[str] = ..., device_name: _Optional[str] = ..., os_version: _Optional[str] = ..., app_version: _Optional[str] = ..., extra: _Optional[_Mapping[str, str]] = ...) -> None: ...

class AllowedApp(_message.Message):
    __slots__ = ("id", "code", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    code: str
    name: str
    def __init__(self, id: _Optional[str] = ..., code: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class UserData(_message.Message):
    __slots__ = ("id", "role", "name", "email", "avatar_url", "allowed_apps")
    ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    AVATAR_URL_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_APPS_FIELD_NUMBER: _ClassVar[int]
    id: str
    role: str
    name: str
    email: str
    avatar_url: str
    allowed_apps: _containers.RepeatedCompositeFieldContainer[AllowedApp]
    def __init__(self, id: _Optional[str] = ..., role: _Optional[str] = ..., name: _Optional[str] = ..., email: _Optional[str] = ..., avatar_url: _Optional[str] = ..., allowed_apps: _Optional[_Iterable[_Union[AllowedApp, _Mapping]]] = ...) -> None: ...

class ValidateTokenRequest(_message.Message):
    __slots__ = ("access_token",)
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    access_token: str
    def __init__(self, access_token: _Optional[str] = ...) -> None: ...

class ValidateTokenResponse(_message.Message):
    __slots__ = ("is_valid", "user", "error")
    IS_VALID_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    is_valid: bool
    user: UserData
    error: str
    def __init__(self, is_valid: bool = ..., user: _Optional[_Union[UserData, _Mapping]] = ..., error: _Optional[str] = ...) -> None: ...

class EmailLoginRequest(_message.Message):
    __slots__ = ("email", "password", "client_id", "device_info", "ip_address", "fcm_token")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    FCM_TOKEN_FIELD_NUMBER: _ClassVar[int]
    email: str
    password: str
    client_id: str
    device_info: DeviceInfo
    ip_address: str
    fcm_token: str
    def __init__(self, email: _Optional[str] = ..., password: _Optional[str] = ..., client_id: _Optional[str] = ..., device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., ip_address: _Optional[str] = ..., fcm_token: _Optional[str] = ...) -> None: ...

class FirebaseLoginRequest(_message.Message):
    __slots__ = ("firebase_token", "client_id", "device_info", "ip_address", "fcm_token")
    FIREBASE_TOKEN_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    FCM_TOKEN_FIELD_NUMBER: _ClassVar[int]
    firebase_token: str
    client_id: str
    device_info: DeviceInfo
    ip_address: str
    fcm_token: str
    def __init__(self, firebase_token: _Optional[str] = ..., client_id: _Optional[str] = ..., device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., ip_address: _Optional[str] = ..., fcm_token: _Optional[str] = ...) -> None: ...

class LoginResponse(_message.Message):
    __slots__ = ("success", "error", "sso_token", "access_token", "refresh_token", "token_type", "expires_in", "user")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    SSO_TOKEN_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOKEN_TYPE_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error: str
    sso_token: str
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserData
    def __init__(self, success: bool = ..., error: _Optional[str] = ..., sso_token: _Optional[str] = ..., access_token: _Optional[str] = ..., refresh_token: _Optional[str] = ..., token_type: _Optional[str] = ..., expires_in: _Optional[int] = ..., user: _Optional[_Union[UserData, _Mapping]] = ...) -> None: ...

class RefreshTokenRequest(_message.Message):
    __slots__ = ("refresh_token", "device_id")
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    refresh_token: str
    device_id: str
    def __init__(self, refresh_token: _Optional[str] = ..., device_id: _Optional[str] = ...) -> None: ...

class RefreshResponse(_message.Message):
    __slots__ = ("success", "error", "access_token", "refresh_token", "token_type", "expires_in")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    REFRESH_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TOKEN_TYPE_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error: str
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    def __init__(self, success: bool = ..., error: _Optional[str] = ..., access_token: _Optional[str] = ..., refresh_token: _Optional[str] = ..., token_type: _Optional[str] = ..., expires_in: _Optional[int] = ...) -> None: ...

class SSOExchangeRequest(_message.Message):
    __slots__ = ("sso_token", "client_id", "device_info", "ip_address", "fcm_token")
    SSO_TOKEN_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    FCM_TOKEN_FIELD_NUMBER: _ClassVar[int]
    sso_token: str
    client_id: str
    device_info: DeviceInfo
    ip_address: str
    fcm_token: str
    def __init__(self, sso_token: _Optional[str] = ..., client_id: _Optional[str] = ..., device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., ip_address: _Optional[str] = ..., fcm_token: _Optional[str] = ...) -> None: ...

class LogoutRequest(_message.Message):
    __slots__ = ("user_id", "client_id", "device_id")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    GLOBAL_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    client_id: str
    device_id: str
    def __init__(self, user_id: _Optional[str] = ..., client_id: _Optional[str] = ..., device_id: _Optional[str] = ..., **kwargs) -> None: ...

class LogoutResponse(_message.Message):
    __slots__ = ("success", "error", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error: str
    message: str
    def __init__(self, success: bool = ..., error: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class GetSessionsRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class SessionInfo(_message.Message):
    __slots__ = ("device_id", "device_info", "ip_address", "client_id", "created_at", "last_activity")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_ACTIVITY_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    device_info: DeviceInfo
    ip_address: str
    client_id: str
    created_at: _timestamp_pb2.Timestamp
    last_activity: _timestamp_pb2.Timestamp
    def __init__(self, device_id: _Optional[str] = ..., device_info: _Optional[_Union[DeviceInfo, _Mapping]] = ..., ip_address: _Optional[str] = ..., client_id: _Optional[str] = ..., created_at: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ..., last_activity: _Optional[_Union[_timestamp_pb2.Timestamp, _Mapping]] = ...) -> None: ...

class GetSessionsResponse(_message.Message):
    __slots__ = ("sessions", "total_clients", "total_sessions")
    SESSIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CLIENTS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_SESSIONS_FIELD_NUMBER: _ClassVar[int]
    sessions: _containers.RepeatedCompositeFieldContainer[SessionInfo]
    total_clients: int
    total_sessions: int
    def __init__(self, sessions: _Optional[_Iterable[_Union[SessionInfo, _Mapping]]] = ..., total_clients: _Optional[int] = ..., total_sessions: _Optional[int] = ...) -> None: ...
