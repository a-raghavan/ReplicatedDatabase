from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetAllKeysReply(_message.Message):
    __slots__ = ["KVpairs", "errormsg"]
    ERRORMSG_FIELD_NUMBER: _ClassVar[int]
    KVPAIRS_FIELD_NUMBER: _ClassVar[int]
    KVpairs: _containers.RepeatedCompositeFieldContainer[KVpair]
    errormsg: str
    def __init__(self, errormsg: _Optional[str] = ..., KVpairs: _Optional[_Iterable[_Union[KVpair, _Mapping]]] = ...) -> None: ...

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
