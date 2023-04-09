from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetAllKeysReply(_message.Message):
    __slots__ = ["KVpairs", "entries", "errormsg", "role"]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    ERRORMSG_FIELD_NUMBER: _ClassVar[int]
    KVPAIRS_FIELD_NUMBER: _ClassVar[int]
    KVpairs: _containers.RepeatedCompositeFieldContainer[KVpair]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    entries: _containers.RepeatedCompositeFieldContainer[LogEntry]
    errormsg: str
    role: str
    def __init__(self, errormsg: _Optional[str] = ..., KVpairs: _Optional[_Iterable[_Union[KVpair, _Mapping]]] = ..., role: _Optional[str] = ..., entries: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ...) -> None: ...

class GetReply(_message.Message):
    __slots__ = ["errormsg", "value"]
    ERRORMSG_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    errormsg: str
    value: str
    def __init__(self, errormsg: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ["key"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class KVpair(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class LogEntry(_message.Message):
    __slots__ = ["command", "key", "term", "value"]
    COMMAND_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    command: str
    key: str
    term: int
    value: str
    def __init__(self, command: _Optional[str] = ..., key: _Optional[str] = ..., value: _Optional[str] = ..., term: _Optional[int] = ...) -> None: ...

class PutReply(_message.Message):
    __slots__ = ["errormsg"]
    ERRORMSG_FIELD_NUMBER: _ClassVar[int]
    errormsg: str
    def __init__(self, errormsg: _Optional[str] = ...) -> None: ...

class PutRequest(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
