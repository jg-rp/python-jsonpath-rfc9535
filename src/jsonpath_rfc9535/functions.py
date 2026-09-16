# pyright: reportIncompatibleMethodOverride=false
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence, Sized
from typing import TYPE_CHECKING, Any, Literal

import regex as re
from iregexp_check import check

from ._nothing import NOTHING

if TYPE_CHECKING:
    from .node import NodeList

LOGICAL_TYPE: Literal[1] = 1
NODES_TYPE: Literal[2] = 2
VALUE_TYPE: Literal[3] = 3

type ExpressionType = Literal[1, 2, 3]
"""An integer indicating a function extension argument type or return type."""


class FunctionExtension(ABC):
    """The base class for all JSONPath function extensions."""

    @property
    @abstractmethod
    def arg_types(self) -> Sequence[ExpressionType]:
        """Argument types expected by this filter function."""

    @property
    @abstractmethod
    def return_type(self) -> ExpressionType:
        """The type of this function extension's return value."""

    @abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """Call the function extension."""


# These standard function extensions are defined by the RFC.


class Count(FunctionExtension):
    arg_types: Sequence[ExpressionType] = [NODES_TYPE]
    return_type: ExpressionType = VALUE_TYPE

    def __call__(self, nodes: NodeList) -> int:
        return len(nodes)


class Length(FunctionExtension):
    arg_types: Sequence[ExpressionType] = [VALUE_TYPE]
    return_type: ExpressionType = VALUE_TYPE

    def __call__(self, obj: Sized) -> object:
        try:
            return len(obj)
        except TypeError:
            return NOTHING


class Match(FunctionExtension):
    arg_types: Sequence[ExpressionType] = [VALUE_TYPE, VALUE_TYPE]
    return_type: ExpressionType = LOGICAL_TYPE

    def __call__(self, string: str, pattern: object) -> object:
        # TODO: cache pattern check and map_re
        if not (isinstance(pattern, str) and check(pattern)):
            return False

        try:
            # re.fullmatch caches compiled patterns internally
            return bool(re.fullmatch(map_re(pattern), string))
        except (TypeError, re.error):
            return False


class Search(FunctionExtension):
    arg_types: Sequence[ExpressionType] = [VALUE_TYPE, VALUE_TYPE]
    return_type: ExpressionType = LOGICAL_TYPE

    def __call__(self, string: str, pattern: object) -> object:
        # TODO: cache pattern check and map_re
        if not (isinstance(pattern, str) and check(pattern)):
            return False

        try:
            # re.search caches compiled patterns internally
            return bool(re.search(map_re(pattern), string, re.VERSION1))
        except (TypeError, re.error):
            return False


class Value(FunctionExtension):
    arg_types: Sequence[ExpressionType] = [NODES_TYPE]
    return_type: ExpressionType = VALUE_TYPE

    def __call__(self, nodes: NodeList) -> object:
        if len(nodes) == 1:
            return nodes[0][0]
        return NOTHING


def map_re(pattern: str) -> str:
    escaped = False
    char_class = False
    parts: list[str] = []
    for ch in pattern:
        if escaped:
            parts.append(ch)
            escaped = False
            continue

        if ch == ".":
            if not char_class:
                parts.append(r"(?:(?![\r\n])\P{Cs}|\p{Cs}\p{Cs})")
            else:
                parts.append(ch)
        elif ch == "\\":
            escaped = True
            parts.append(ch)
        elif ch == "[":
            char_class = True
            parts.append(ch)
        elif ch == "]":
            char_class = False
            parts.append(ch)
        else:
            parts.append(ch)

    return "".join(parts)
