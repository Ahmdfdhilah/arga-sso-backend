import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class User(_message.Message):
    __slots__ = ("id", "name", "email", "phone", "avatar_path", "status", "role", "created_at", "updated_at", "alias", "gender", "date_of_birth", "address", "bio")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PHONE_FIELD_NUMBER: _ClassVar[int]
    AVATAR_PATH_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    ALIAS_FIELD_NUMBER: _ClassVar[int]
    GENDER_FIELD_NUMBER: _ClassVar[int]
    DATE_OF_BIRTH_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    BIO_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    email: str
    phone: str
    avatar_path: str
    status: str
    role: str
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    alias: str
    gender: str
    date_of_birth: _timestamp_pb2.Timestamp
    address: str
    bio: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., email: _Optional[str] = ..., phone: _Optional[str] = ..., avatar_path: _Optional[str] = ..., status: _Optional[str] = ..., role: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., alias: _Optional[str] = ..., gender: _Optional[str] = ..., date_of_birth: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., address: _Optional[str] = ..., bio: _Optional[str] = ...) -> None: ...

class GetUserRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class GetUserByEmailRequest(_message.Message):
    __slots__ = ("email",)
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    email: str
    def __init__(self, email: _Optional[str] = ...) -> None: ...

class GetUserByPhoneRequest(_message.Message):
    __slots__ = ("phone",)
    PHONE_FIELD_NUMBER: _ClassVar[int]
    phone: str
    def __init__(self, phone: _Optional[str] = ...) -> None: ...

class BatchGetUsersRequest(_message.Message):
    __slots__ = ("user_ids",)
    USER_IDS_FIELD_NUMBER: _ClassVar[int]
    user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, user_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class BatchGetUsersResponse(_message.Message):
    __slots__ = ("users",)
    USERS_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[User]
    def __init__(self, users: _Optional[_Iterable[_Union[User, _Mapping]]] = ...) -> None: ...

class UserResponse(_message.Message):
    __slots__ = ("found", "user")
    FOUND_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    found: bool
    user: User
    def __init__(self, found: bool = ..., user: _Optional[_Union[User, _Mapping]] = ...) -> None: ...
