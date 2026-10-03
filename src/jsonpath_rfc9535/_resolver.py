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
        data: object,
    ) -> Iterable[Node]: ...


class BasicResolver(Protocol):
    def resolve(
        self,
        env: JSONPathEnvironment,
        segments: Sequence[Segment],
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
        if type(left) is NodeList:
            if len(left) == 0:
                left = NOTHING
            elif len(left) == 1:
                left = left[0][0]
            else:
                return False
        elif type(left) is BasicNodeList:
            if len(left) == 0:
                left = NOTHING
            elif len(left) == 1:
                left = left[0]
            else:
                return False

        if type(right) is NodeList:
            if len(right) == 0:
                right = NOTHING
            elif len(right) == 1:
                right = right[0][0]
            else:
                return False
        elif type(right) is BasicNodeList:
            if len(right) == 0:
                right = NOTHING
            elif len(right) == 1:
                right = right[0]
            else:
                return False

        if left is NOTHING and right is NOTHING:
            return True

        # Remember 1 == True and 0 == False in Python
        if isinstance(left, bool):
            return isinstance(right, bool) and left == right

        if isinstance(right, bool):
            return False

        return left == right

    def lt(self, left: object, right: object) -> bool:
        if type(left) is NodeList:
            if len(left) == 1:
                left = left[0][0]
            else:
                return False
        elif type(left) is BasicNodeList:
            if len(left) == 1:
                left = left[0]
            else:
                return False

        if type(right) is NodeList:
            if len(right) == 1:
                right = right[0][0]
            else:
                return False
        elif type(right) is BasicNodeList:
            if len(right) == 1:
                right = right[0]
            else:
                return False

        if isinstance(left, str) and isinstance(right, str):
            return left < right

        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left < right

        return False
