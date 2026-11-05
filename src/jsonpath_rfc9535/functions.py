# pyright: reportIncompatibleMethodOverride=false
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence, Sized
from typing import TYPE_CHECKING, Any, Literal

import regex as re

from ._iregexp import check_iregexp, map_iregexp
from ._lru_cache import LRUCache, ThreadSafeLRUCache
from ._node import BasicNodeList
from ._nothing import NOTHING
from .exceptions import JSONPathError

if TYPE_CHECKING:
    from ._node import NodeList

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


class CachingRegexFunction(FunctionExtension):
    INVALID_PATTERN: Literal[1] = 1

    arg_types: Sequence[ExpressionType] = [VALUE_TYPE, VALUE_TYPE]
    return_type: ExpressionType = LOGICAL_TYPE

    def __init__(
        self,
        *,
        cache_capacity: int = 300,
        debug: bool = False,
        escape_anchors: bool = False,
        thread_safe: bool = False,
    ) -> None:
        super().__init__()
        self.cache: LRUCache[str, re.Pattern[str] | Literal[1]] = (
            ThreadSafeLRUCache(capacity=cache_capacity)
            if thread_safe
            else LRUCache(capacity=cache_capacity)
        )

        self.debug = debug
        self.escape_anchors = escape_anchors

    def __call__(self, string: object, pattern: object) -> bool:
        if not isinstance(pattern, str):
            return self._debug_or_false("pattern is not a string")

        if not isinstance(string, str):
            return self._debug_or_false("object is not a string")

        pattern_ = self.cache.get(pattern)

        if pattern_ == self.INVALID_PATTERN:
            return self._debug_or_false("invalid pattern from cache")

        if pattern_ is None:
            if not check_iregexp(pattern):
                self.cache[pattern] = self.INVALID_PATTERN
                return self._debug_or_false("I-Regexp check failed")

            try:
                pattern_ = re.compile(
                    map_iregexp(
                        pattern,
                        escape_anchors=self.escape_anchors,
                        wrap=False,
                    ),
                    re.VERSION1,
                )
            except re.error as err:
                self.cache[pattern] = self.INVALID_PATTERN
                return self._debug_or_false(str(err))

            self.cache[pattern] = pattern_

        return self.go(pattern_, string)

    def _debug_or_false(self, message: str) -> bool:
        if self.debug:
            raise JSONPathError(f"{self.__class__.__name__}: {message}")
        return False

    def go(self, pattern: re.Pattern[str], string: str) -> bool:
        raise NotImplementedError


class Match(CachingRegexFunction):
    arg_types: Sequence[ExpressionType] = [VALUE_TYPE, VALUE_TYPE]
    return_type: ExpressionType = LOGICAL_TYPE

    def go(self, pattern: re.Pattern[str], string: str) -> bool:
        return bool(pattern.fullmatch(string))


class Search(CachingRegexFunction):
    arg_types: Sequence[ExpressionType] = [VALUE_TYPE, VALUE_TYPE]
    return_type: ExpressionType = LOGICAL_TYPE

    def go(self, pattern: re.Pattern[str], string: str) -> bool:
        return bool(pattern.search(string))


class Value(FunctionExtension):
    arg_types: Sequence[ExpressionType] = [NODES_TYPE]
    return_type: ExpressionType = VALUE_TYPE

    def __call__(self, nodes: NodeList | BasicNodeList) -> object:
        if len(nodes) == 1:
            return nodes[0] if isinstance(nodes, BasicNodeList) else nodes[0][0]
        return NOTHING
