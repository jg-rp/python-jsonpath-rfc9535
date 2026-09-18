from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Protocol

from ._ast import Segment

if TYPE_CHECKING:
    from .environment import JSONPathEnvironment
    from .node import Node


class Resolver(Protocol):
    def resolve(
        self,
        env: JSONPathEnvironment,
        segments: Sequence[Segment],
        root: str,
        data: object,
    ) -> Iterable[Node]: ...


class BasicResolver(Protocol):
    def resolve(
        self,
        env: JSONPathEnvironment,
        segments: Sequence[Segment],
        root: str,
        data: object,
    ) -> Iterable[object]: ...
