from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

T = TypeVar('T', str, Literal[''])


class Symbol:
    pass


@dataclass
class Name(Symbol, Generic[T]):
    name: T


class Wildcard(Symbol):
    pass