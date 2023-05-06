from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Bandeja(_message.Message):
    __slots__ = ["correos"]
    CORREOS_FIELD_NUMBER: _ClassVar[int]
    correos: _containers.RepeatedCompositeFieldContainer[Correo]
    def __init__(self, correos: _Optional[_Iterable[_Union[Correo, _Mapping]]] = ...) -> None: ...

class Correo(_message.Message):
    __slots__ = ["a", "contenido", "desde", "id", "leido"]
    A_FIELD_NUMBER: _ClassVar[int]
    CONTENIDO_FIELD_NUMBER: _ClassVar[int]
    DESDE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LEIDO_FIELD_NUMBER: _ClassVar[int]
    a: str
    contenido: str
    desde: str
    id: int
    leido: bool
    def __init__(self, id: _Optional[int] = ..., desde: _Optional[str] = ..., a: _Optional[str] = ..., leido: bool = ..., contenido: _Optional[str] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class EnviarMensajeRequest(_message.Message):
    __slots__ = ["correo", "token", "usuario"]
    CORREO_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    USUARIO_FIELD_NUMBER: _ClassVar[int]
    correo: Correo
    token: str
    usuario: str
    def __init__(self, usuario: _Optional[str] = ..., token: _Optional[str] = ..., correo: _Optional[_Union[Correo, _Mapping]] = ...) -> None: ...

class GetBandejaRequest(_message.Message):
    __slots__ = ["bandeja", "token", "usuario"]
    BANDEJA_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    USUARIO_FIELD_NUMBER: _ClassVar[int]
    bandeja: str
    token: str
    usuario: str
    def __init__(self, usuario: _Optional[str] = ..., token: _Optional[str] = ..., bandeja: _Optional[str] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ["passwd", "usuario"]
    PASSWD_FIELD_NUMBER: _ClassVar[int]
    USUARIO_FIELD_NUMBER: _ClassVar[int]
    passwd: str
    usuario: str
    def __init__(self, usuario: _Optional[str] = ..., passwd: _Optional[str] = ...) -> None: ...

class MensajeActionRequest(_message.Message):
    __slots__ = ["bandeja", "correo_id", "token", "usuario"]
    BANDEJA_FIELD_NUMBER: _ClassVar[int]
    CORREO_ID_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    USUARIO_FIELD_NUMBER: _ClassVar[int]
    bandeja: str
    correo_id: int
    token: str
    usuario: str
    def __init__(self, usuario: _Optional[str] = ..., token: _Optional[str] = ..., correo_id: _Optional[int] = ..., bandeja: _Optional[str] = ...) -> None: ...

class Status(_message.Message):
    __slots__ = ["detalles", "success"]
    DETALLES_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    detalles: str
    success: bool
    def __init__(self, success: bool = ..., detalles: _Optional[str] = ...) -> None: ...
