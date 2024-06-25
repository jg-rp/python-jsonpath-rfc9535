"""JSONPath child and descendant segment definitions."""

from __future__ import annotations

import random
from abc import ABC
from abc import abstractmethod
from collections import deque
from typing import TYPE_CHECKING
from typing import Deque
from typing import Iterable
from typing import Tuple

from .exceptions import JSONPathRecursionError

if TYPE_CHECKING:
    from .environment import JSONPathEnvironment
    from .node import JSONPathNode
    from .selectors import JSONPathSelector
    from .tokens import Token


class JSONPathSegment(ABC):
    """Base class for all JSONPath segments."""

    __slots__ = ("env", "token", "selectors")

    def __init__(
        self,
        *,
        env: JSONPathEnvironment,
        token: Token,
        selectors: Tuple[JSONPathSelector, ...],
    ) -> None:
        self.env = env
        self.token = token
        self.selectors = selectors

    @abstractmethod
    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Apply this segment to each `JSONPathNode` in _nodes_."""


class JSONPathChildSegment(JSONPathSegment):
    """The JSONPath child selection segment."""

    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Select children of each node in _nodes_."""
        for node in nodes:
            for selector in self.selectors:
                yield from selector.resolve(node)

    def __str__(self) -> str:
        return f"[{', '.join(str(itm) for itm in self.selectors)}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, JSONPathChildSegment)
            and self.selectors == __value.selectors
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash((self.selectors, self.token))


class JSONPathRecursiveDescentSegment(JSONPathSegment):
    """The JSONPath recursive descent segment."""

    def resolve(self, nodes: Iterable[JSONPathNode]) -> Iterable[JSONPathNode]:
        """Select descendants of each node in _nodes_."""
        visitor = (
            self._nondeterministic_visit if self.env.nondeterministic else self._visit
        )

        for node in nodes:
            for _node in visitor(node):
                for selector in self.selectors:
                    yield from selector.resolve(_node)

    def _visit(self, node: JSONPathNode, depth: int = 1) -> Iterable[JSONPathNode]:
        """Depth-first, pre-order node traversal."""
        if depth > self.env.max_recursion_depth:
            raise JSONPathRecursionError("recursion limit exceeded", token=self.token)

        yield node

        if isinstance(node.value, dict):
            for name, val in node.value.items():
                if isinstance(val, (dict, list)):
                    _node = node.new_child(val, name)
                    yield from self._visit(_node, depth + 1)
        elif isinstance(node.value, list):
            for i, element in enumerate(node.value):
                if isinstance(element, (dict, list)):
                    _node = node.new_child(element, i)
                    yield from self._visit(_node, depth + 1)

    def _nondeterministic_visit(
        self,
        root: JSONPathNode,
        depth: int = 1,
    ) -> Iterable[JSONPathNode]:
        """Nondeterministic node traversal."""
        # (node, depth) tuples
        queue: Deque[Tuple[JSONPathNode, int]] = deque()

        # Visit the root node
        yield root

        # Queue root's children
        queue.extend([(child, depth) for child in _nondeterministic_children(root)])

        while queue:
            node, depth = queue.popleft()
            yield node

            if depth >= self.env.max_recursion_depth:
                raise JSONPathRecursionError(
                    "recursion limit exceeded", token=self.token
                )

            # Randomly choose to visit child nodes now or queue them for later?
            visit_children = random.choice([True, False])  # noqa: S311

            for child in _nondeterministic_children(node):
                if visit_children:
                    yield child

                    # Queue grandchildren by randomly interleaving them into the
                    # queue while maintaining queue and grandchild order.
                    grandchildren = [
                        (child, depth + 2)
                        for child in _nondeterministic_children(child)
                    ]

                    queue = deque(
                        [
                            next(n)
                            for n in random.sample(
                                [iter(queue)] * len(queue)
                                + [iter(grandchildren)] * len(grandchildren),
                                len(queue) + len(grandchildren),
                            )
                        ]
                    )
                else:
                    queue.append((child, depth + 1))

    def __str__(self) -> str:
        return f"..[{', '.join(str(itm) for itm in self.selectors)}]"

    def __eq__(self, __value: object) -> bool:
        return (
            isinstance(__value, JSONPathRecursiveDescentSegment)
            and self.selectors == __value.selectors
            and self.token == __value.token
        )

    def __hash__(self) -> int:
        return hash(("..", self.selectors, self.token))


def _nondeterministic_children(node: JSONPathNode) -> Iterable[JSONPathNode]:
    """Yield children of _node_ with nondeterministic object/dict iteration."""
    if isinstance(node.value, dict):
        items = list(node.value.items())
        random.shuffle(items)
        for name, val in items:
            yield node.new_child(val, name)
    elif isinstance(node.value, list):
        for i, element in enumerate(node.value):
            yield node.new_child(element, i)
