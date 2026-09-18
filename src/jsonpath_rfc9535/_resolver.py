from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Protocol

from ._ast import Segment
from ._node import BasicNodeList, Node, NodeList
from ._nothing import NOTHING

if TYPE_CHECKING:
    from ._environment import JSONPathEnvironment


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


class Resolver_:
    def truthy(self, obj: object) -> bool:
        if isinstance(obj, BasicNodeList | NodeList):
            return len(obj) > 0
        if obj is NOTHING:
            return False
        if obj is None:
            return True
        return bool(obj)

    def eq(self, left: object, right: object) -> bool:
        if isinstance(right, BasicNodeList | NodeList):
            left, right = right, left

        if isinstance(left, BasicNodeList):
            if isinstance(right, BasicNodeList):
                return left == right
            if len(left) == 0:
                return right is NOTHING
            if len(left) == 1:
                return left[0] == right
            return False

        if left is NOTHING and right is NOTHING:
            return True

        # Remember 1 == True and 0 == False in Python
        if isinstance(right, bool):
            left, right = right, left

        if isinstance(left, bool):
            return isinstance(right, bool) and left == right

        return left == right

    def lt(self, left: object, right: object) -> bool:
        if isinstance(left, str) and isinstance(right, str):
            return left < right

        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left < right

        return False
