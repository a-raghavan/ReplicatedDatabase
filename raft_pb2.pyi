from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AppendEntriesRequest(_message.Message):
    __slots__ = ["commitindex", "currentterm", "entries", "previousterm", "prevlogindex"]
    COMMITINDEX_FIELD_NUMBER: _ClassVar[int]
    CURRENTTERM_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    PREVIOUSTERM_FIELD_NUMBER: _ClassVar[int]
    PREVLOGINDEX_FIELD_NUMBER: _ClassVar[int]
    commitindex: int
    currentterm: int
    entries: _containers.RepeatedCompositeFieldContainer[LogEntry]
    previousterm: int
    prevlogindex: int
    def __init__(self, prevlogindex: _Optional[int] = ..., entries: _Optional[_Iterable[_Union[LogEntry, _Mapping]]] = ..., commitindex: _Optional[int] = ..., currentterm: _Optional[int] = ..., previousterm: _Optional[int] = ...) -> None: ...

class AppendEntriesResponse(_message.Message):
    __slots__ = ["success", "term"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    TERM_FIELD_NUMBER: _ClassVar[int]
    success: bool
    term: int
    def __init__(self, term: _Optional[int] = ..., success: bool = ...) -> None: ...

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

class RequestVoteRequest(_message.Message):
    __slots__ = ["candidateId", "currentterm", "lastLogIndex", "lastLogTerm"]
    CANDIDATEID_FIELD_NUMBER: _ClassVar[int]
    CURRENTTERM_FIELD_NUMBER: _ClassVar[int]
    LASTLOGINDEX_FIELD_NUMBER: _ClassVar[int]
    LASTLOGTERM_FIELD_NUMBER: _ClassVar[int]
    candidateId: str
    currentterm: int
    lastLogIndex: int
    lastLogTerm: int
    def __init__(self, candidateId: _Optional[str] = ..., currentterm: _Optional[int] = ..., lastLogIndex: _Optional[int] = ..., lastLogTerm: _Optional[int] = ...) -> None: ...

class RequestVoteResponse(_message.Message):
    __slots__ = ["term", "voteGranted"]
    TERM_FIELD_NUMBER: _ClassVar[int]
    VOTEGRANTED_FIELD_NUMBER: _ClassVar[int]
    term: int
    voteGranted: bool
    def __init__(self, term: _Optional[int] = ..., voteGranted: bool = ...) -> None: ...
