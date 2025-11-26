"""JSONPath selector definitions."""

from __future__ import annotations

import random
from abc import ABC
from abc import abstractmethod
from contextlib import suppress
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Optional
from typing import Sequence

from .exceptions import JSONPathIndexError
from .exceptions import JSONPathTypeError
from .filter_expressions import FilterContext
from .serialize import canonical_string

if TYPE_CHECKING:
    from .environment import JSONPathEnvironment
    from .filter_expressions import FilterExpression
    from .node import JSONPathNode
    from .tokens import Token


class JSONPathSelector(ABC):
    """Base class for all JSONPath selectors."""

    __slots__ = ("env", "token")

    def __init__(self, *, env: JSONPathEnvironment, token: Token) -> None:
        self.env = env
        self.token = token

    @abstractmethod
    def resolve(self, node: JSONPathNode) -> Iterable[JSONPathNode]:
        """Apply the segment/selector to _node_.

        Arguments:
            node: A node matched by preceding segments/selectors.

        Returns:
            The `JSONPathNode` instances created by applying this selector to _node_.
        """


class NameSelector(JSONPathSelector):
    """The name selector."""

    __slots__ = ("name",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        name: str,
    ) -> None:
        super().__init__(env=env, token=token)
        self.name = name

    def __str__(self) -> str:
        return canonical_string(self.name)

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, NameSelector)
            and self.name == __value.name
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.name, self.token))

    def resolve(self, node: JSONPathNode) -> Iterable[JSONPathNode]:
        """Select a value from a dict/object by its property/key."""
        if isinstance(node.value, dict):
            with suppress(KeyError):
                yield node.new_child(node.value[self.name], self.name, node)


class IndexSelector(JSONPathSelector):
    """The array index selector."""

    __slots__ = ("index", "_as_key")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        index: int,
    ) -> None:
        if index < env.min_int_index or index > env.max_int_index:
            raise JSONPathIndexError("index out of range", token=token)

        super().__init__(env=env, token=token)
        self.index = index
        self._as_key = str(self.index)

    def __str__(self) -> str:
        return str(self.index)

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, IndexSelector)
            and self.index == __value.index
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.index, self.token))

    def _normalized_index(self, obj: Sequence[object]) -> int:
        if self.index < 0 and len(obj) >= abs(self.index):
            return len(obj) + self.index
        return self.index

    def resolve(self, node: JSONPathNode) -> Iterable[JSONPathNode]:
        """Select an element from an array by index."""
        if isinstance(node.value, list):
            norm_index = self._normalized_index(node.value)
            with suppress(IndexError):
                yield node.new_child(node.value[self.index], norm_index, node)


class SliceSelector(JSONPathSelector):
    """Array/List slicing selector."""

    __slots__ = ("slice",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        step: Optional[int] = None,
    ) -> None:
        super().__init__(env=env, token=token)
        self._check_range(start, stop, step)
        self.slice = slice(start, stop, step)

    def __str__(self) -> str:
        stop = self.slice.stop if self.slice.stop is not None else ""
        start = self.slice.start if self.slice.start is not None else ""
        step = self.slice.step if self.slice.step is not None else "1"
        return f"{start}:{stop}:{step}"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, SliceSelector)
            and self.slice == __value.slice
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((str(self), self.token))

    def _check_range(self, *indices: Optional[int]) -> None:
        for i in indices:
            if i is not None and (
                i < self.env.min_int_index or i > self.env.max_int_index
            ):
                raise JSONPathIndexError("index out of range", token=self.token)

    def resolve(self, node: JSONPathNode) -> Iterable[JSONPathNode]:
        """Select a range of values from an array/list."""
        if isinstance(node.value, list) and self.slice.step != 0:
            for idx, element in zip(  # noqa: B905
                range(*self.slice.indices(len(node.value))), node.value[self.slice]
            ):
                yield node.new_child(element, idx, node)


class WildcardSelector(JSONPathSelector):
    """The wildcard selector."""

    def __init__(self, *, env: JSONPathEnvironment, token: Token) -> None:
        super().__init__(env=env, token=token)

    def __str__(self) -> str:
        return "*"

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, WildcardSelector) and self.token == __value.token

    def __hash__(self) -> int:
        return hash(self.token)

    def resolve(self, node: JSONPathNode) -> Iterable[JSONPathNode]:
        """Select all elements from a array/list or values from a dict/object."""
        if isinstance(node.value, dict):
            if self.env.nondeterministic:
                _members = list(node.value.items())
                random.shuffle(_members)
                members: Iterable[Any] = iter(_members)
            else:
                members = node.value.items()

            for name, val in members:
                yield node.new_child(val, name, node)

        elif isinstance(node.value, list):
            for i, element in enumerate(node.value):
                yield node.new_child(element, i, node)


class FilterSelector(JSONPathSelector):
    """Filter array/list items or dict/object values with a filter expression."""

    __slots__ = ("expression",)

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        expression: FilterExpression,
    ) -> None:
        super().__init__(env=env, token=token)
        self.expression = expression

    def __str__(self) -> str:
        return f"?{self.expression}"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, FilterSelector)
            and self.expression == __value.expression
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((str(self.expression), self.token))

    def resolve(self, node: JSONPathNode) -> Iterable[JSONPathNode]:  # noqa: PLR0912
        """Select array/list items or dict/object values where with a filter."""
        if isinstance(node.value, dict):
            if self.env.nondeterministic:
                _members = list(node.value.items())
                random.shuffle(_members)
                members: Iterable[Any] = iter(_members)
            else:
                members = node.value.items()

            for name, val in members:
                context = FilterContext(
                    env=self.env,
                    current=val,
                    root=node.root,
                )
                try:
                    if self.expression.evaluate(context):
                        yield node.new_child(val, name, node)
                except JSONPathTypeError as err:
                    if not err.token:
                        err.token = self.token
                    raise

        elif isinstance(node.value, list):
            for i, element in enumerate(node.value):
                context = FilterContext(
                    env=self.env,
                    current=element,
                    root=node.root,
                )
                try:
                    if self.expression.evaluate(context):
                        yield node.new_child(element, i, node)
                except JSONPathTypeError as err:
                    if not err.token:
                        err.token = self.token
                    raise
