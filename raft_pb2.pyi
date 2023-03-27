from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AppendEntriesReply(_message.Message):
    __slots__ = ["success", "term"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    success: bool
    term: int
    def __init__(self, term: _Optional[int] = ..., success: bool = ...) -> None: ...

class AppendEntriesRequest(_message.Message):
    __slots__ = ["commitindex", "entries", "prevlogindex", "term"]
    COMMITINDEX_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    PREVLOGINDEX_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    commitindex: int
    entries: _containers.RepeatedCompositeFieldContainer[ReplicatedLogEntry]
    prevlogindex: int
    term: int
    def __init__(self, prevlogindex: _Optional[int] = ..., entries: _Optional[_Iterable[_Union[ReplicatedLogEntry, _Mapping]]] = ..., commitindex: _Optional[int] = ..., term: _Optional[int] = ...) -> None: ...

class ReplicatedLogEntry(_message.Message):
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
